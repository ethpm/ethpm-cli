from argparse import Namespace
import copy
import json
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple

from eth_typing import URI
from eth_utils import to_dict, to_int, to_text, to_tuple
from eth_utils.toolz import assoc, dissoc
from ethpm.backends.ipfs import BaseIPFSBackend
from ethpm.backends.registry import is_valid_registry_uri, parse_registry_uri
from ethpm.uri import is_ipfs_uri

from ethpm_cli._utils.filesystem import atomic_replace, is_package_installed
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.shellart import bold_blue, bold_green, bold_white
from ethpm_cli.commands.package import InstalledPackage, Package
from ethpm_cli.commands.registry import get_active_registry
from ethpm_cli.config import Config
from ethpm_cli.constants import (
    ETHPM_PACKAGES_DIR,
    LOCKFILE_NAME,
    REGISTRY_STORE,
    SRC_DIR_NAME,
)
from ethpm_cli.exceptions import InstallError
from ethpm_cli.validation import validate_parent_directory, validate_same_registry

logger = logging.getLogger("ethpm_cli.install")


def install_package(package: Package, config: Config) -> None:
    if is_package_installed(package.alias, config):
        raise InstallError(
            f"Installation conflict: Package: '{package.manifest['package_name']}' "
            f"aliased to '{package.alias}' already installed on the filesystem at "
            f"{config.ethpm_dir / package.alias}. Try installing this package with "
            "a different alias."
        )

    # Create temporary package directory
    tmp_package_dir = Path(tempfile.mkdtemp())
    write_package_installation_files(package, tmp_package_dir, config.ipfs_backend)

    # Copy temp package directory to ethpm dir namespace
    dest_package_dir = config.ethpm_dir / package.alias
    validate_parent_directory(config.ethpm_dir, dest_package_dir)
    shutil.copytree(tmp_package_dir, dest_package_dir)
    install_to_ethpm_lock(package, (config.ethpm_dir / LOCKFILE_NAME))


class InstalledPackageTree(NamedTuple):
    depth: int
    path: Path
    manifest: Dict[str, Any]
    children: Tuple[Any, ...]  # Expects InstalledPackageTree
    content_hash: str

    @property
    def package_name(self) -> str:
        return self.manifest["package_name"]

    @property
    def package_version(self) -> str:
        return self.manifest["version"]

    @property
    def format_for_display(self) -> str:
        prefix = "- " * self.depth
        if self.path.name != self.package_name:
            alias = f" (alias: {bold_blue(self.path.name)})"
        else:
            alias = ""
        main_info = (
            f"{prefix}{bold_blue(self.package_name)}{alias}"
            f"=={bold_green(self.package_version)}"
        )
        hash_info = f"({bold_white(self.content_hash)})"
        if self.children:
            children = "\n" + "\n".join(
                (child.format_for_display for child in self.children)
            )
        else:
            children = ""
        return f"{main_info} --- {hash_info}{children}"


def list_installed_packages(config: Config) -> None:
    installed_packages = [
        get_installed_package_tree(base_dir)
        for base_dir in config.ethpm_dir.iterdir()
        if base_dir.is_dir()
    ]
    for package in sorted(installed_packages):
        logger.info(package.format_for_display)


def get_installed_package_tree(base_dir: Path, depth: int = 0) -> InstalledPackageTree:
    manifest = json.loads((base_dir / "manifest.json").read_text())
    ethpm_lock = json.loads((base_dir.parent / LOCKFILE_NAME).read_text())
    content_hash = ethpm_lock[base_dir.name]["resolved_uri"]
    dependency_dirs = get_dependency_dirs(base_dir)
    children = tuple(
        get_installed_package_tree(dependency_dir, depth + 1)
        for dependency_dir in dependency_dirs
    )
    return InstalledPackageTree(depth, base_dir, manifest, children, content_hash)


@to_tuple
def get_dependency_dirs(base_dir: Path) -> Iterable[Path]:
    dep_dir = base_dir / ETHPM_PACKAGES_DIR
    if dep_dir.is_dir():
        for ddir in dep_dir.iterdir():
            if ddir.is_dir():
                yield ddir


@to_tuple
def get_package_aliases(package_name: str, config: Config) -> Iterable[Tuple[str, ...]]:
    lockfile_path = config.ethpm_dir / "ethpm.lock"
    if lockfile_path.is_file():
        lockfile = json.loads(lockfile_path.read_text())
        all_aliases = [
            (package_data["alias"], package_data["resolved_package_name"])
            for package_data in lockfile.values()
        ]
        for alias, resolved_package_name in all_aliases:
            if resolved_package_name == package_name:
                yield alias


def resolve_installed_package_by_id(
    package_id: str, config: Config
) -> InstalledPackage:
    lockfile_path = config.ethpm_dir / "ethpm.lock"
    lockfile = json.loads(lockfile_path.read_text())
    return InstalledPackage(**lockfile[package_id])


def update_package(args: Namespace, config: Config) -> None:
    if not is_package_installed(args.package, config):
        check_for_aliased_package(args.package, config)
        return

    installed_package = resolve_installed_package_by_id(args.package, config)
    active_registry = get_active_registry(config.xdg_ethpmcli_root / REGISTRY_STORE)
    if is_valid_registry_uri(installed_package.install_uri):
        validate_same_registry(installed_package.install_uri, active_registry.uri)

    connected_chain_id = config.w3.eth.chainId
    active_registry_uri = parse_registry_uri(active_registry.uri)
    if not to_int(text=active_registry_uri.chain_id) == connected_chain_id:
        raise InstallError(
            f"Registry URI chain: {active_registry_uri.chain_id} doesn't match "
            f"connected web3: {connected_chain_id}."
        )

    config.w3.pm.set_registry(active_registry_uri.address)
    all_package_names = config.w3.pm.get_all_package_names()
    if installed_package.resolved_package_name not in all_package_names:
        raise InstallError(
            f"{installed_package.resolved_package_name} is not available on the active registry "
            f"{active_registry.uri}. Available packages include: {all_package_names}."
        )

    all_release_data = config.w3.pm.get_all_package_releases(
        installed_package.resolved_package_name
    )
    all_versions = [version for version, _ in all_release_data]

    if installed_package.resolved_version not in all_versions:
        raise InstallError(
            f"{installed_package.resolved_package_name}@{installed_package.resolved_version} not "
            f"found on the active registry {active_registry.uri}."
        )

    on_chain_install_uri = pluck_release_data(
        all_release_data, installed_package.resolved_version
    )
    if on_chain_install_uri != installed_package.resolved_uri:
        raise InstallError(
            f"Install URI found on active registry for {installed_package.resolved_package_name}@"
            f"{installed_package.resolved_version}: {on_chain_install_uri} does not match the "
            f"install URI found in local lockfile: {installed_package.resolved_uri}."
        )

    cli_logger.info(
        f"{len(all_versions)} versions of {installed_package.resolved_package_name} "
        f"found: {all_versions} \n"
        f"On the active registry: {active_registry.uri}"
    )
    count = 0
    while True:
        count += 1
        target_version = input("Please enter the version you want to install. ")
        if count > 5:
            raise InstallError("Max attempts (5) reached. ")
        elif target_version == installed_package.resolved_version:
            cli_logger.info(f"Version already installed: {target_version}. ")
        elif target_version not in all_versions:
            cli_logger.info(f"Version unavailable: {target_version}. ")
        else:
            break

    # Create an updated args/Package for new install
    updated_args = copy.deepcopy(args)
    if installed_package.resolved_package_name != args.package:
        updated_args.alias = args.package
    updated_args.uri = pluck_release_data(all_release_data, target_version)
    updated_args.package_version = target_version
    updated_package = Package(updated_args, config.ipfs_backend)

    # atomic replace
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_ethpm_dir = Path(tmpdir) / ETHPM_PACKAGES_DIR
        shutil.copytree(config.ethpm_dir, tmp_ethpm_dir)
        tmp_config = copy.copy(config)
        tmp_config.ethpm_dir = tmp_ethpm_dir
        uninstall_package(args.package, tmp_config)
        install_package(updated_package, tmp_config)
        shutil.rmtree(config.ethpm_dir)
        tmp_ethpm_dir.replace(config.ethpm_dir)

    cli_logger.info(
        f"{updated_args.package} successfully updated to version "
        f"{updated_args.package_version}."
    )


def pluck_release_data(
    all_release_data: List[str], target_version: str
) -> Optional[URI]:
    for version, uri in all_release_data:
        if version == target_version:
            return URI(uri)
    return None


def uninstall_package(package_name: str, config: Config) -> None:
    if not is_package_installed(package_name, config):
        check_for_aliased_package(package_name, config)
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_package_dir = Path(tmpdir) / ETHPM_PACKAGES_DIR
        shutil.copytree(config.ethpm_dir, tmp_package_dir)
        shutil.rmtree(tmp_package_dir / package_name)
        uninstall_from_ethpm_lock(package_name, (tmp_package_dir / LOCKFILE_NAME))
        shutil.rmtree(config.ethpm_dir)
        tmp_package_dir.replace(config.ethpm_dir)


def check_for_aliased_package(package_name: str, config: Config) -> None:
    aliases = get_package_aliases(package_name, config)
    if aliases:
        raise InstallError(
            f"Found {package_name} installed under the alias(es): {aliases}. "
            "To uninstall an aliased package, use the alias as the uninstall argument."
        )
    else:
        raise InstallError(
            f"No package with the name {package_name} found installed under {config.ethpm_dir}."
        )


def write_package_installation_files(
    package: Package, tmp_package_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    (tmp_package_dir / "manifest.json").touch()
    (tmp_package_dir / "manifest.json").write_bytes(package.raw_manifest)

    write_sources_to_disk(package, tmp_package_dir, ipfs_backend)
    write_docs_to_disk(package, tmp_package_dir, ipfs_backend)
    write_build_deps_to_disk(package, tmp_package_dir, ipfs_backend)
    tmp_ethpm_lock = tmp_package_dir.parent / LOCKFILE_NAME
    install_to_ethpm_lock(package, tmp_ethpm_lock)


def write_sources_to_disk(
    package: Package, package_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    sources = resolve_sources(package, ipfs_backend)
    for path, source_contents in sources.items():
        target_file = package_dir / SRC_DIR_NAME / path
        target_dir = target_file.parent
        if not target_dir.is_dir():
            target_dir.mkdir(parents=True)
        target_file.touch()
        validate_parent_directory((package_dir / SRC_DIR_NAME), target_file)
        target_file.write_text(source_contents)


@to_dict
def resolve_sources(
    package: Package, ipfs_backend: BaseIPFSBackend
) -> Iterable[Tuple[str, str]]:
    for path, source in package.manifest["sources"].items():
        if is_ipfs_uri(source):
            contents = to_text(ipfs_backend.fetch_uri_contents(source)).rstrip("\n")
        else:
            # for inlined sources
            contents = source
        yield path, contents


def write_docs_to_disk(
    package: Package, package_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    try:
        doc_uri = package.manifest["meta"]["links"]["documentation"]
    except KeyError:
        return

    if is_ipfs_uri(doc_uri):
        documentation = ipfs_backend.fetch_uri_contents(doc_uri)
        doc_path = package_dir / "documentation.md"
        doc_path.touch()
        doc_path.write_bytes(documentation)


def write_build_deps_to_disk(
    package: Package, package_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    if "build_dependencies" in package.manifest:
        child_ethpm_dir = package_dir / ETHPM_PACKAGES_DIR
        child_ethpm_dir.mkdir()
        for name, uri in package.manifest["build_dependencies"].items():
            dep_package = Package(Namespace(uri=uri, alias=""), ipfs_backend)
            tmp_dep_dir = child_ethpm_dir / name
            tmp_dep_dir.mkdir()
            validate_parent_directory(package_dir, tmp_dep_dir)
            write_package_installation_files(dep_package, tmp_dep_dir, ipfs_backend)


def install_to_ethpm_lock(package: Package, ethpm_lock: Path) -> None:
    if ethpm_lock.is_file():
        old_lock = json.loads(ethpm_lock.read_text())
    else:
        old_lock = {}
        ethpm_lock.touch()
    new_package_data = package.generate_ethpm_lock()
    new_lock = assoc(old_lock, package.alias, new_package_data)
    ethpm_lock.write_text(f"{json.dumps(new_lock, sort_keys=True, indent=4)}\n")


def uninstall_from_ethpm_lock(package_name: str, ethpm_lock: Path) -> None:
    old_lock = json.loads(ethpm_lock.read_text())
    new_lock = dissoc(old_lock, package_name)
    with atomic_replace(ethpm_lock) as ethpm_lock_file:
        ethpm_lock_file.write(json.dumps(new_lock, sort_keys=True, indent=4))
        ethpm_lock_file.write("\n")

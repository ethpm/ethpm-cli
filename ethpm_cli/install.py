import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Dict, Iterable, NamedTuple, Tuple

from eth_utils import to_dict, to_text, to_tuple
from eth_utils.toolz import assoc, dissoc
from ethpm.backends.ipfs import BaseIPFSBackend
from ethpm.uri import is_ipfs_uri

from ethpm_cli._utils.filesystem import atomic_replace
from ethpm_cli.config import Config
from ethpm_cli.constants import ETHPM_PACKAGES_DIR, LOCKFILE_NAME, SRC_DIR_NAME
from ethpm_cli.exceptions import InstallError
from ethpm_cli.package import Package
from ethpm_cli.validation import validate_parent_directory

logger = logging.getLogger("ethpm_cli.install")


def install_package(pkg: Package, config: Config) -> None:
    if is_package_installed(pkg.alias, config):
        raise InstallError(
            f"Installation conflict: Package: '{pkg.manifest['package_name']}' "
            f"aliased to '{pkg.alias}' already installed on the filesystem at "
            f"{config.ethpm_dir / pkg.alias}. Try installing this package with "
            "a different alias."
        )

    # Create temporary package directory
    tmp_pkg_dir = Path(tempfile.mkdtemp())
    write_pkg_installation_files(pkg, tmp_pkg_dir, config.ipfs_backend)

    # Copy temp package directory to ethpm dir namespace
    dest_pkg_dir = config.ethpm_dir / pkg.alias
    validate_parent_directory(config.ethpm_dir, dest_pkg_dir)
    shutil.copytree(tmp_pkg_dir, dest_pkg_dir)
    install_to_ethpm_lock(pkg, (config.ethpm_dir / LOCKFILE_NAME))


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
            alias = f" @ {self.path.name}"
        else:
            alias = ""
        main_info = f"{prefix}{self.package_name}{alias}=={self.package_version}"
        hash_info = f"({self.content_hash})"
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
    for pkg in sorted(installed_packages):
        logger.info(pkg.format_for_display)


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


def is_package_installed(package_name: str, config: Config) -> bool:
    return os.path.exists(config.ethpm_dir / package_name)


@to_tuple
def get_package_aliases(package_name: str, config: Config) -> Iterable[Tuple[str, ...]]:
    lockfile_path = config.ethpm_dir / "ethpm.lock"
    if lockfile_path.is_file():
        lockfile = json.loads(lockfile_path.read_text())
        all_aliases = [
            (pkg_data["alias"], pkg_data["resolved_package_name"])
            for pkg_data in lockfile.values()
        ]
        for alias, resolved_pkg_name in all_aliases:
            if resolved_pkg_name == package_name:
                yield alias


def uninstall_package(package_name: str, config: Config) -> None:
    if is_package_installed(package_name, config):
        tmp_pkg_dir = Path(tempfile.mkdtemp()) / ETHPM_PACKAGES_DIR
        shutil.copytree(config.ethpm_dir, tmp_pkg_dir)
        shutil.rmtree(tmp_pkg_dir / package_name)
        uninstall_from_ethpm_lock(package_name, (tmp_pkg_dir / LOCKFILE_NAME))

        shutil.rmtree(config.ethpm_dir)
        tmp_pkg_dir.replace(config.ethpm_dir)
        return

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


def write_pkg_installation_files(
    pkg: Package, tmp_pkg_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    (tmp_pkg_dir / "manifest.json").touch()
    (tmp_pkg_dir / "manifest.json").write_bytes(pkg.raw_manifest)

    write_sources_to_disk(pkg, tmp_pkg_dir, ipfs_backend)
    write_docs_to_disk(pkg, tmp_pkg_dir, ipfs_backend)
    write_build_deps_to_disk(pkg, tmp_pkg_dir, ipfs_backend)
    tmp_ethpm_lock = tmp_pkg_dir.parent / LOCKFILE_NAME
    install_to_ethpm_lock(pkg, tmp_ethpm_lock)


def write_sources_to_disk(
    pkg: Package, pkg_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    sources = resolve_sources(pkg, ipfs_backend)
    for path, source_contents in sources.items():
        target_file = pkg_dir / SRC_DIR_NAME / path
        target_dir = target_file.parent
        if not target_dir.is_dir():
            target_dir.mkdir(parents=True)
        target_file.touch()
        validate_parent_directory((pkg_dir / SRC_DIR_NAME), target_file)
        target_file.write_text(source_contents)


@to_dict
def resolve_sources(
    pkg: Package, ipfs_backend: BaseIPFSBackend
) -> Iterable[Tuple[str, str]]:
    for path, source in pkg.manifest["sources"].items():
        if is_ipfs_uri(source):
            contents = to_text(ipfs_backend.fetch_uri_contents(source)).rstrip("\n")
        else:
            # for inlined sources
            contents = source
        yield path, contents


def write_docs_to_disk(
    pkg: Package, pkg_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    try:
        doc_uri = pkg.manifest["meta"]["links"]["documentation"]
    except KeyError:
        return

    if is_ipfs_uri(doc_uri):
        documentation = ipfs_backend.fetch_uri_contents(doc_uri)
        doc_path = pkg_dir / "documentation.md"
        doc_path.touch()
        doc_path.write_bytes(documentation)


def write_build_deps_to_disk(
    pkg: Package, pkg_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    if "build_dependencies" in pkg.manifest:
        child_ethpm_dir = pkg_dir / ETHPM_PACKAGES_DIR
        child_ethpm_dir.mkdir()
        for name, uri in pkg.manifest["build_dependencies"].items():
            dep_pkg = Package(uri, "", ipfs_backend)
            tmp_dep_dir = child_ethpm_dir / name
            tmp_dep_dir.mkdir()
            validate_parent_directory(pkg_dir, tmp_dep_dir)
            write_pkg_installation_files(dep_pkg, tmp_dep_dir, ipfs_backend)


def install_to_ethpm_lock(pkg: Package, ethpm_lock: Path) -> None:
    if ethpm_lock.is_file():
        old_lock = json.loads(ethpm_lock.read_text())
    else:
        old_lock = {}
        ethpm_lock.touch()
    new_pkg_data = pkg.generate_ethpm_lock()
    new_lock = assoc(old_lock, pkg.alias, new_pkg_data)
    ethpm_lock.write_text(f"{json.dumps(new_lock, sort_keys=True, indent=4)}\n")


def uninstall_from_ethpm_lock(package_name: str, ethpm_lock: Path) -> None:
    old_lock = json.loads(ethpm_lock.read_text())
    new_lock = dissoc(old_lock, package_name)
    with atomic_replace(ethpm_lock) as ethpm_lock_file:
        ethpm_lock_file.write(json.dumps(new_lock, sort_keys=True, indent=4))
        ethpm_lock_file.write("\n")

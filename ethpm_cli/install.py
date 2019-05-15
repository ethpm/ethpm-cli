from argparse import Namespace
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Iterable, Tuple

from eth_utils import to_dict, to_list, to_text
from eth_utils.toolz import assoc, dissoc
from ethpm.backends.ipfs import BaseIPFSBackend
from ethpm.utils.ipfs import is_ipfs_uri

from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli.constants import ETHPM_DIR_NAME
from ethpm_cli.exceptions import InstallError
from ethpm_cli.package import Package
from ethpm_cli.validation import validate_parent_directory

logger = logging.getLogger("ethpm_cli.install")


class Config:
    """
    Class to manage CLI config options
    - IPFS Backend
    - Target ethpm_dir
    """

    def __init__(self, args: Namespace) -> None:
        if "local_ipfs" in args:
            self.ipfs_backend = get_ipfs_backend(args.local_ipfs)
        else:
            self.ipfs_backend = get_ipfs_backend(True)

        if args.ethpm_dir is None:
            self.ethpm_dir = Path.cwd() / ETHPM_DIR_NAME
            if not self.ethpm_dir.is_dir():
                self.ethpm_dir.mkdir()
        else:
            self.ethpm_dir = args.ethpm_dir


def install_package(pkg: Package, config: Config) -> None:
    if is_package_installed(pkg.alias, config):
        raise InstallError(
            "Installation conflict: A directory or file already exists at the install location "
            f"for the package '{pkg.manifest['package_name']}' aliased to '{pkg.alias}' on the "
            f"filesystem at {config.ethpm_dir / pkg.alias}."
        )

    # Create temporary package directory
    tmp_pkg_dir = Path(tempfile.mkdtemp())
    write_pkg_installation_files(pkg, tmp_pkg_dir, config.ipfs_backend)

    # Copy temp package directory to ethpm dir namespace
    dest_pkg_dir = config.ethpm_dir / pkg.alias
    validate_parent_directory(config.ethpm_dir, dest_pkg_dir)
    shutil.copytree(tmp_pkg_dir, dest_pkg_dir)
    install_to_ethpm_lock(pkg, (config.ethpm_dir / "ethpm.lock"))


def list_installed_packages(config: Config) -> None:
    for pkg_data in get_installed_packages(config.ethpm_dir):
        logger.info(pkg_data)


@to_list
def get_installed_packages(ethpm_dir: Path) -> Iterable[str]:
    installed_pkgs = reversed(sorted(ethpm_dir.glob("**/manifest.json")))
    for manifest_path in installed_pkgs:
        manifest = json.loads(manifest_path.read_text())
        num_deep = str(manifest_path.relative_to(ethpm_dir)).count("/")
        yield f"{num_deep * '--'} <Package {manifest['package_name']}=={manifest['version']}>"


def is_package_installed(package_name: str, config: Config) -> bool:
    return os.path.exists(config.ethpm_dir / package_name)


def uninstall_package(package_name: str, config: Config) -> None:
    if not is_package_installed(package_name, config):
        raise InstallError(
            f"Unable to uninstall {package_name} from {config.ethpm_dir}"
        )

    shutil.rmtree(config.ethpm_dir / package_name)
    uninstall_from_ethpm_lock(package_name, (config.ethpm_dir / "ethpm.lock"))


def write_pkg_installation_files(
    pkg: Package, tmp_pkg_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    (tmp_pkg_dir / "manifest.json").touch()
    (tmp_pkg_dir / "manifest.json").write_bytes(pkg.raw_manifest)

    write_sources_to_disk(pkg, tmp_pkg_dir, ipfs_backend)
    write_build_deps_to_disk(pkg, tmp_pkg_dir, ipfs_backend)
    tmp_ethpm_lock = tmp_pkg_dir.parent / "ethpm.lock"
    install_to_ethpm_lock(pkg, tmp_ethpm_lock)


def write_sources_to_disk(
    pkg: Package, pkg_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    sources = resolve_sources(pkg, ipfs_backend)
    for path, source_contents in sources.items():
        target_file = pkg_dir / "src" / path
        target_dir = target_file.parent
        if not target_dir.is_dir():
            target_dir.mkdir(parents=True)
        target_file.touch()
        validate_parent_directory((pkg_dir / "src"), target_file)
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


def write_build_deps_to_disk(
    pkg: Package, pkg_dir: Path, ipfs_backend: BaseIPFSBackend
) -> None:
    if "build_dependencies" in pkg.manifest:
        child_ethpm_dir = pkg_dir / ETHPM_DIR_NAME
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
    ethpm_lock.write_text(f"{json.dumps(new_lock, sort_keys=True, indent=4)}\n")

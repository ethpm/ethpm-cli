from ethpm.typing import Manifest
from eth_utils import to_text
from ethpm.backends.ipfs import BaseIPFSBackend
from ethpm.utils.ipfs import is_ipfs_uri
import json
from pathlib import Path
from typing import Dict

from eth_utils.toolz import assoc
from ethpm.typing import URI

from ethpm_cli.exceptions import InstallError
from ethpm_cli.package import Package
from ethpm_cli._utils.ipfs import get_ipfs_backend


class Manager:
    def __init__(self, target_dir: Path = None, ipfs: bool = None) -> None:
        self.ethpm_dir = process_target_dir(target_dir)
        self.ethpm_lock = self.ethpm_dir / "ethpm.lock"
        self.ipfs_backend = get_ipfs_backend(ipfs)

    def install(self, target_uri: URI, alias: str = None) -> None:
        target_pkg = Package(target_uri, alias, self.ipfs_backend)
        pkg_path = self.ethpm_dir / target_pkg.alias
        if pkg_path.is_dir():
            raise InstallError(f"{target_pkg.alias} is already installed.")
        pkg_path.mkdir()
        install_pkg(target_pkg, pkg_path, self.ipfs_backend)
        update_ethpm_lock(target_pkg, self.ethpm_lock)


def install_pkg(pkg: Package, pkg_path: Path, ipfs: BaseIPFSBackend) -> None:
    (pkg_path / "manifest.json").touch()
    (pkg_path / "manifest.json").write_bytes(pkg.raw_manifest)
    if "sources" in pkg.manifest:
        write_sources_to_disk(pkg.manifest, pkg_path, ipfs)
    if "build_dependencies" in pkg.manifest:
        write_build_deps_to_disk(pkg.manifest["build_dependencies"], pkg_path)


def update_ethpm_lock(pkg: Package, ethpm_lock: Path) -> None:
    if ethpm_lock.is_file():
        old_lock = json.loads(ethpm_lock.read_text())
    else:
        old_lock = {}
        ethpm_lock.touch()
    new_pkg_data = pkg.generate_ethpm_lock()
    new_lock = assoc(old_lock, pkg.alias, new_pkg_data)
    ethpm_lock.write_text(json.dumps(new_lock, sort_keys=True, indent=4))


def write_build_deps_to_disk(build_deps: Dict[str, str], ethpm_dir: Path) -> None:
    dep_manager = Manager(ethpm_dir)
    for dep in build_deps.values():
        dep_manager.install(dep)


def write_sources_to_disk(
    manifest: Manifest, parent_dir: Path, ipfs: BaseIPFSBackend
) -> None:
    (parent_dir / "src").mkdir()
    for path, source in manifest["sources"].items():
        if is_ipfs_uri(source):
            source_contents = to_text(ipfs.fetch_uri_contents(source)).rstrip("\n")
        else:
            # for inlined sources
            source_contents = source
        target_file = parent_dir / "src" / path
        target_dir = target_file.parent
        if not target_dir.is_dir():
            target_dir.mkdir(parents=True)
        target_file.touch()
        target_file.write_text(source_contents)


def process_target_dir(target_dir: Path) -> Path:
    if not target_dir:
        ethpm_dir = Path.cwd() / "ethpm_packages"
    else:
        if not target_dir.is_dir():
            raise InstallError(f"Provided directory: {target_dir} was not found.")
        ethpm_dir = target_dir / "ethpm_packages"

    if not ethpm_dir.is_dir():
        ethpm_dir.mkdir()
    return ethpm_dir

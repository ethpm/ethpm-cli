import json
from pathlib import Path

from eth_utils import to_text
from eth_utils.toolz import assoc
from ethpm.typing import URI
from ethpm.utils.ipfs import is_ipfs_uri

from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli.exceptions import InstallError
from ethpm_cli.package import Package


class Manager:
    def __init__(self, target_dir: Path = None, ipfs: bool = None) -> None:
        self.ethpm_dir = process_target_dir(target_dir)
        self.ethpm_lock = self.ethpm_dir / "ethpm.lock"
        self.ipfs_backend = get_ipfs_backend(ipfs)

    def install(self, target_uri: URI, alias: str = None) -> None:
        target_pkg = Package(target_uri, self.ipfs_backend, alias)
        pkg_path = self.ethpm_dir / target_pkg.alias
        if pkg_path.is_dir():
            raise InstallError(f"{target_pkg.alias} is already installed.")
        pkg_path.mkdir()
        (pkg_path / "manifest.json").touch()
        (pkg_path / "manifest.json").write_bytes(target_pkg.raw_manifest)
        self.write_pkg_to_disk(target_pkg, pkg_path)
        update_ethpm_lock(target_pkg, self.ethpm_lock)

    def write_pkg_to_disk(self, pkg: Package, ethpm_dir: Path) -> None:
        if "sources" in pkg.manifest:
            self.write_sources_to_disk(pkg, ethpm_dir)

        if "build_dependencies" in pkg.manifest:
            self.write_build_deps_to_disk(pkg, ethpm_dir)

    def write_sources_to_disk(self, pkg: Package, ethpm_dir: Path) -> None:
        (ethpm_dir / "src").mkdir()
        for path, source in pkg.manifest["sources"].items():
            if is_ipfs_uri(source):
                source_contents = to_text(
                    self.ipfs_backend.fetch_uri_contents(source)
                ).rstrip("\n")
            else:
                # for inlined sources
                source_contents = source
            target_file = ethpm_dir / "src" / path
            target_dir = target_file.parent
            if not target_dir.is_dir():
                target_dir.mkdir(parents=True)
            target_file.touch()
            target_file.write_text(source_contents)

    def write_build_deps_to_disk(self, pkg: Package, ethpm_dir: Path) -> None:
        dep_manager = Manager(ethpm_dir)
        for dep in pkg.manifest["build_dependencies"].values():
            dep_manager.install(dep)


def update_ethpm_lock(pkg: Package, ethpm_lock: Path) -> None:
    if ethpm_lock.is_file():
        old_lock = json.loads(ethpm_lock.read_text())
    else:
        old_lock = {}
        ethpm_lock.touch()
    new_pkg_data = pkg.generate_ethpm_lock()
    new_lock = assoc(old_lock, pkg.alias, new_pkg_data)
    ethpm_lock.write_text(json.dumps(new_lock, sort_keys=True, indent=4))


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

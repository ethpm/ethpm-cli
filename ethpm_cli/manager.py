import json
import os
from pathlib import Path
from urllib import parse

from eth_utils import to_text, to_dict
from ethpm.backends.ipfs import LocalIPFSBackend, InfuraIPFSBackend
from ethpm.backends.http import GithubOverHTTPSBackend
from ethpm.backends.registry import RegistryURIBackend
from ethpm.utils.uri import is_valid_content_addressed_github_uri
from ethpm.validation import is_valid_registry_uri, validate_package_name
from ethpm.utils.manifest_validation import (
    validate_raw_manifest_format,
    validate_manifest_against_schema,
    validate_manifest_deployments,
)
from ethpm.utils.ipfs import is_ipfs_uri, generate_file_hash, extract_ipfs_path_from_uri
from ethpm.utils.uri import validate_blob_uri_contents

from ethpm_cli.exceptions import InstallError
from ethpm_cli.install import write_sources_to_disk


class Manager:
    def __init__(self, target_dir=None, ipfs=None):
        self.ethpm_dir = process_target_dir(target_dir)
        self.ipfs_backend = get_ipfs_backend(ipfs)
        # needs to be updated to get installed packages from ethpm lock
        self.installed_pkgs = get_installed_pkgs(self.ethpm_dir)

    def install(self, target_uri, alias=None):
        target_pkg = Package(target_uri, alias)
        if alias:
            pkg_path = self.ethpm_dir / alias
        else:
            pkg_path = self.ethpm_dir / target_pkg.manifest["package_name"]
        if pkg_path.is_dir():
            raise InstallError(
                f"{target_pkg.manifest['package_name']} already installed."
            )
        pkg_path.mkdir()
        # Installing the package
        install_pkg(target_pkg, pkg_path)
        install_ethpm_lock(target_pkg, self.ethpm_dir)
        # Handle ethpm.lock
        self.installed_pkgs.append(target_pkg.manifest["package_name"])


def install_ethpm_lock(pkg, ethpm_dir):
    ethpm_lock = ethpm_dir / "ethpm.lock"
    ethpm_lock.touch()
    ethpm_lock_content = pkg.generate_ethpm_lock()
    ethpm_lock.write_text(json.dumps(ethpm_lock_content, sort_keys=True, indent=4))


def install_pkg(pkg, pkg_path):
    (pkg_path / "manifest.json").touch()
    (pkg_path / "manifest.json").write_bytes(pkg.raw_manifest)
    if "sources" in pkg.manifest:
        write_sources_to_disk(pkg.manifest, pkg_path)
    # todo build deps


class Package:
    def __init__(self, target_uri, alias=None):
        self.alias = alias
        self.target_uri = target_uri
        self.manifest_uri = None
        self.raw_manifest = None
        self.manifest = None
        self.registry_address = None
        self.resolved_content_hash = None

        # do we need all this uri validation
        validate_supported_uri(target_uri)
        if self.alias:
            validate_package_name(alias)
        self.resolve_target_uri()
        self.resolve_manifest_uri()
        # validate resolved contents

    @to_dict
    def generate_ethpm_lock(self):
        yield "resolved_uri", self.manifest_uri
        yield "resolved_content_hash", self.resolved_content_hash
        yield "target_uri", self.target_uri
        yield "registry_address", self.registry_address
        yield "alias", self.alias
        yield "resolved_version", self.manifest["version"]
        yield "resolved_package_name", self.manifest["package_name"]

    def resolve_target_uri(self):
        if is_valid_registry_uri(self.target_uri):
            self.registry_address = parse.urlparse(self.target_uri).netloc
            self.manifest_uri = RegistryURIBackend().fetch_uri_contents(self.target_uri)
        elif is_valid_content_addressed_github_uri(self.target_uri) or is_ipfs_uri(
            self.target_uri
        ):
            self.manifest_uri = self.target_uri
        else:
            raise Exception

    def resolve_manifest_uri(self):
        if is_valid_content_addressed_github_uri(self.manifest_uri):
            # test this path & rstrip?
            self.raw_manifest = GithubOverHTTPSBackend().fetch_uri_contents(
                self.manifest_uri
            )
            validate_blob_uri_contents(self.raw_manifest, self.manifest_uri)
            self.resolved_content_hash = parse.urlparse(self.manifest_uri).path.split(
                "/"
            )[-1]

        elif is_ipfs_uri(self.manifest_uri):
            self.raw_manifest = LocalIPFSBackend().fetch_uri_contents(self.manifest_uri)
            self.resolved_content_hash = generate_file_hash(self.raw_manifest)
            manifest_content_hash = extract_ipfs_path_from_uri(self.manifest_uri)
            if self.resolved_content_hash != manifest_content_hash:
                raise Exception

        else:
            raise Exception
        self.manifest = process_and_validate_raw_manifest(
            to_text(self.raw_manifest).rstrip("\n")
        )


def process_and_validate_raw_manifest(raw_manifest):
    validate_raw_manifest_format(raw_manifest)
    manifest = json.loads(raw_manifest)
    validate_manifest_against_schema(manifest)
    validate_manifest_deployments(manifest)
    return manifest


def get_ipfs_backend(ipfs):
    if ipfs:
        # update to support custom ports
        return LocalIPFSBackend()
    return InfuraIPFSBackend()


def validate_supported_uri(uri):
    if (
        not is_ipfs_uri(uri)
        and not is_valid_registry_uri(uri)  # noqa: W503
        and not is_valid_content_addressed_github_uri(uri)  # noqa: W503
    ):
        raise Exception("unsupported uri")


def process_target_dir(target_dir):
    if not target_dir:
        ethpm_dir = Path(os.getcwd()) / "ethpm_packages"
    else:
        if not Path(target_dir).is_dir():
            raise InstallError(f"Provided directory: {target_dir} was not found.")
        ethpm_dir = Path(target_dir) / "ethpm_packages"

    if not ethpm_dir.is_dir():
        ethpm_dir.mkdir()
    return ethpm_dir


def get_installed_pkgs(ethpm_dir):
    if not (ethpm_dir / "ethpm.lock").is_file():
        return []
    ethpm_lock = json.loads((ethpm_dir / "ethpm.lock").read_text())
    return [ethpm_lock["resolved_package_name"]]

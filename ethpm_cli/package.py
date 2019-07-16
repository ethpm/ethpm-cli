from collections import namedtuple
import json
from typing import Any, Dict, Iterable, Tuple  # noqa: F401
from urllib import parse

from eth_typing import URI, Address, Manifest  # noqa: F401
from eth_utils import to_dict, to_text
from ethpm._utils.ipfs import extract_ipfs_path_from_uri
from ethpm.backends.http import GithubOverHTTPSBackend
from ethpm.backends.ipfs import BaseIPFSBackend
from ethpm.backends.registry import RegistryURIBackend, parse_registry_uri
from ethpm.validation.manifest import (
    validate_manifest_against_schema,
    validate_manifest_deployments,
    validate_raw_manifest_format,
)

from ethpm_cli.exceptions import UriNotSupportedError


class Package:
    def __init__(
        self, install_uri: URI, alias: str, ipfs_backend: BaseIPFSBackend
    ) -> None:
        self.ipfs_backend = ipfs_backend
        resolved_install_uri = resolve_install_uri(install_uri)
        self.manifest_uri: URI = resolved_install_uri.manifest_uri
        self.registry_address: Address = resolved_install_uri.registry_address
        resolved_manifest_uri = resolve_manifest_uri(
            self.manifest_uri, self.ipfs_backend
        )
        self.raw_manifest: bytes = resolved_manifest_uri.raw_manifest
        self.resolved_content_hash: str = resolved_manifest_uri.resolved_content_hash

        self.manifest: Manifest = process_and_validate_raw_manifest(self.raw_manifest)
        self.alias = alias if alias else self.manifest["package_name"]
        self.install_uri = install_uri

    @to_dict
    def generate_ethpm_lock(self) -> Iterable[Tuple[str, Any]]:
        yield "resolved_uri", self.manifest_uri
        yield "resolved_content_hash", self.resolved_content_hash
        yield "install_uri", self.install_uri
        yield "registry_address", self.registry_address
        yield "alias", self.alias
        yield "resolved_version", self.manifest["version"]
        yield "resolved_package_name", self.manifest["package_name"]


ResolvedInstallURI = namedtuple(
    "ResolvedInstallURI", ["manifest_uri", "registry_address"]
)
ResolvedManifestURI = namedtuple(
    "ResolvedManifestURI", ["raw_manifest", "resolved_content_hash"]
)


def resolve_manifest_uri(uri: URI, ipfs: BaseIPFSBackend) -> ResolvedManifestURI:
    github_backend = GithubOverHTTPSBackend()
    if github_backend.can_resolve_uri(uri):
        raw_manifest = github_backend.fetch_uri_contents(uri)
        resolved_content_hash = parse.urlparse(uri).path.split("/")[-1]
    elif ipfs.can_resolve_uri(uri):
        raw_manifest = ipfs.fetch_uri_contents(uri)
        resolved_content_hash = extract_ipfs_path_from_uri(uri)
    else:
        raise UriNotSupportedError(
            f"{uri} is not supported. Currently EthPM CLI only supports "
            "IPFS and Github blob manifest uris."
        )
    return ResolvedManifestURI(raw_manifest, resolved_content_hash)


def resolve_install_uri(uri: URI) -> ResolvedInstallURI:
    registry_backend = RegistryURIBackend()
    if registry_backend.can_translate_uri(uri):
        # todo: replace with registry_backend.fetch_uri_contents(uri) after next web3 release
        from web3.auto.infura import w3

        registry_address, chain_id, pkg_name, pkg_version = parse_registry_uri(uri)
        if not hasattr(w3, "_pm"):
            w3.enable_unstable_package_management_api()
        w3.pm.set_registry(registry_address)
        _, _, manifest_uri = w3.pm.get_release_data(pkg_name, pkg_version)
    else:
        manifest_uri = uri
        registry_address = None
    return ResolvedInstallURI(manifest_uri, registry_address)


def process_and_validate_raw_manifest(raw_manifest: bytes) -> Manifest:
    raw_manifest_text = to_text(raw_manifest).rstrip("\n")
    validate_raw_manifest_format(raw_manifest_text)
    manifest = json.loads(raw_manifest_text)
    validate_manifest_against_schema(manifest)
    validate_manifest_deployments(manifest)
    return manifest

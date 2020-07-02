import json
from pathlib import Path
from typing import Tuple

from eth_typing import URI
from ethpm.backends.ipfs import BaseIPFSBackend, InfuraIPFSBackend, LocalIPFSBackend
from ethpm.validation.manifest import validate_manifest_against_schema


def pin_local_manifest(manifest_path: Path) -> Tuple[str, str, URI]:
    manifest_output = json.loads(manifest_path.read_text())
    validate_manifest_against_schema(manifest_output)
    package_name = manifest_output["name"]
    package_version = manifest_output["version"]

    ipfs_backend = get_ipfs_backend()
    ipfs_data = ipfs_backend.pin_assets(manifest_path)

    manifest_uri = URI(f"ipfs://{ipfs_data[0]['Hash']}")
    return (package_name, package_version, manifest_uri)


def get_ipfs_backend(ipfs: bool = False) -> BaseIPFSBackend:
    if ipfs:
        return LocalIPFSBackend()
    return InfuraIPFSBackend()

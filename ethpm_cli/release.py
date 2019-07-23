import json

from eth_typing import URI
from ethpm.backends.registry import parse_registry_uri

from ethpm_cli.config import Config, setup_w3
from ethpm_cli.constants import REGISTRY_STORE
from ethpm_cli.exceptions import AuthorizationError
from ethpm_cli.registry import get_active_registry


def release_package(
    package_name: str, version: str, manifest_uri: URI, config: Config
) -> bytes:
    # todo: validate release privileges on registry?
    if not config.private_key:
        raise AuthorizationError("To release a package you must provide the password for your local keyfile.")

    registry_store_data = json.loads((config.ethpm_dir / REGISTRY_STORE).read_text())
    active_registry_uri = get_active_registry(registry_store_data)
    active_registry = parse_registry_uri(active_registry_uri)
    if config.w3.net.version != active_registry.chain_id:
        w3 = setup_w3(active_registry.chain_id, config.private_key)
    else:
        w3 = config.w3
    w3.pm.set_registry(active_registry.address)
    release_id = w3.pm.release_package(package_name, version, manifest_uri)
    return release_id

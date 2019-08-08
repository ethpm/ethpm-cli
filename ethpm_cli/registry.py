import json
from pathlib import Path
from typing import Any, Dict, Iterable, NamedTuple, Optional, Tuple

from eth_typing import URI
from eth_utils import to_tuple
from eth_utils.toolz import assoc, assoc_in, dissoc
from ethpm.backends.registry import is_valid_registry_uri, parse_registry_uri
from ethpm.constants import SUPPORTED_CHAIN_IDS

from ethpm_cli._utils.filesystem import atomic_replace
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.config import Config
from ethpm_cli.constants import REGISTRY_STORE
from ethpm_cli.exceptions import AmbigiousFileSystem, AuthorizationError, InstallError


class StoredRegistry(NamedTuple):
    uri: URI
    active: bool = False
    alias: Optional[str] = None
    ens: Optional[str] = None

    @property
    def format_for_display(self) -> str:
        activated = " (active)" if self.active else ""
        alias = f" --- {self.alias}" if self.alias else ""
        return f"{self.uri}{alias}{activated}"


def deploy_registry(config: Config, alias: str = None) -> str:
    if not config.private_key:
        raise AuthorizationError(
            "To deploy a registry, you must provide the password for your local keyfile."
        )
    chain_id = config.w3.eth.chainId
    chain_name = SUPPORTED_CHAIN_IDS[chain_id]
    cli_logger.info(
        f"Deploying a new registry to {chain_name}, this may take a minute..."
    )
    # todo: handle tx timeout error gracefully
    registry_address = config.w3.pm.deploy_and_set_registry()
    cli_logger.info(f"New registry deployed to {registry_address} on {chain_name}.")
    registry_uri = URI(f"erc1319://{registry_address}:{chain_id}")
    add_registry(registry_uri, alias, config)
    activate_registry(registry_uri, config)
    return registry_address


def list_registries(config: Config) -> None:
    registry_store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    if not registry_store_path.is_file():
        raise AmbigiousFileSystem(
            "No registry store found in ethPM CLI xdg root. "
            "Create one with `ethpm registry add`"
        )
    registry_store = json.loads((config.xdg_ethpmcli_root / REGISTRY_STORE).read_text())
    installed_registries = [
        StoredRegistry(reg, data["active"], data["alias"], data["ens"])
        for reg, data in registry_store.items()
    ]
    for registry in installed_registries:
        cli_logger.info(registry.format_for_display)


def add_registry(registry_uri: URI, alias: Optional[str], config: Config) -> None:
    store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    if not store_path.is_file():
        generate_registry_store(registry_uri, alias, store_path)
    else:
        update_registry_store(registry_uri, alias, store_path)


def remove_registry(uri_or_alias: str, config: Config) -> None:
    store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    if not store_path.is_file():
        raise InstallError(
            f"Unable to remove registry: {uri_or_alias}. "
            f"No registry store found in {config.xdg_ethpmcli_root}."
        )
    registry = resolve_uri_or_alias(uri_or_alias, store_path)
    if registry.active:
        raise InstallError(
            "Unable to remove an active registry. Please activate a different "
            f"registry before removing registry: {registry.uri}."
        )
    old_store_data = json.loads(store_path.read_text())
    updated_store_data = dissoc(old_store_data, registry.uri)
    write_store_data_to_disk(updated_store_data, store_path)


def activate_registry(uri_or_alias: str, config: Config) -> None:
    store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    store_data = json.loads(store_path.read_text())
    registry = resolve_uri_or_alias(uri_or_alias, store_path)
    active_registry = get_active_registry(store_path)
    if registry.uri != active_registry.uri:
        deactivated_store_data = assoc_in(
            store_data, [active_registry.uri, "active"], False
        )
        activated_store_data = assoc_in(
            deactivated_store_data, [registry.uri, "active"], True
        )
        write_store_data_to_disk(activated_store_data, store_path)


def resolve_uri_or_alias(uri_or_alias: str, store_path: Path) -> StoredRegistry:
    if is_valid_registry_uri(uri_or_alias):
        return resolve_uri_and_alias(URI(uri_or_alias), None, store_path)
    else:
        return resolve_uri_and_alias(None, uri_or_alias, store_path)


def resolve_uri_and_alias(
    registry_uri: Optional[URI], alias: Optional[str], store_path: Path
) -> StoredRegistry:
    if (registry_uri and alias) or (not registry_uri and not alias):
        raise InstallError("Cannot resolve both an alias and registry uri.")
    all_registries = get_all_registries(store_path)
    if alias:
        return lookup_registry_by_alias(alias, all_registries)

    all_registry_uris = (reg.uri for reg in all_registries)
    if not registry_uri or registry_uri not in all_registry_uris:
        raise InstallError(
            f"No registry @ {registry_uri} is available in {store_path}."
        )
    for reg in all_registries:
        if reg.uri == registry_uri:
            return reg
    raise InstallError("Cannot resolve registry uri: {registry_uri} or alias: {alias}.")


@to_tuple
def get_all_registries(store_path: Path) -> Iterable[StoredRegistry]:
    store_data = json.loads(store_path.read_text())
    for registry_uri, data in store_data.items():
        yield StoredRegistry(registry_uri, data["active"], data["alias"], data["ens"])


def get_active_registry(store_path: Path) -> StoredRegistry:
    all_registries = get_all_registries(store_path)
    for registry in all_registries:
        if registry.active is True:
            return registry
    raise InstallError("Invalid registry store data found.")


def lookup_registry_by_alias(
    alias: str, all_registries: Tuple[StoredRegistry, ...]
) -> StoredRegistry:
    all_aliases = (registry.alias for registry in all_registries)
    if alias not in all_aliases:
        raise InstallError(
            f"Alias: {alias} not found in registry store. "
            f"Available registry aliases include: {list(all_aliases)}."
        )
    for registry in all_registries:
        if alias == registry.alias:
            return registry
    raise InstallError(f"Unable to lookup registry under the alias: {alias}.")


def generate_registry_store(
    registry_uri: URI, alias: Optional[str], store_path: Path
) -> None:
    store_path.touch()
    init_registry_data = {
        registry_uri: generate_registry_store_data(registry_uri, alias, activate=True)
    }
    write_store_data_to_disk(init_registry_data, store_path)


def update_registry_store(
    registry_uri: URI, alias: Optional[str], store_path: Path
) -> None:
    all_registries = get_all_registries(store_path)
    all_registry_uris = (registry.uri for registry in all_registries)
    if registry_uri in all_registry_uris:
        raise InstallError(f"Registry @ {registry_uri} already stored.")
    old_store_data = json.loads(store_path.read_text())
    new_registry_data = generate_registry_store_data(registry_uri, alias)
    updated_store_data = assoc(old_store_data, registry_uri, new_registry_data)
    write_store_data_to_disk(updated_store_data, store_path)


def write_store_data_to_disk(store_data: Dict[URI, Any], store_path: Path) -> None:
    with atomic_replace(store_path) as f:
        f.write(json.dumps(store_data, indent=4, sort_keys=True))


def generate_registry_store_data(
    registry_uri: URI, alias: Optional[str], activate: bool = False
) -> Dict[str, Any]:
    parsed_uri = parse_registry_uri(registry_uri)
    # todo: support ens in registry uri
    return {
        "ens": None,
        "address": parsed_uri.address,
        "alias": alias,
        "active": activate,
    }

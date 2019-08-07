import json
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional

from eth_typing import URI
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
        return f"{self.uri} --- {self.alias}{activated}"


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


def remove_registry(registry_uri: URI, alias: Optional[str], config: Config) -> None:
    store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    if not store_path.is_file():
        raise InstallError(
            f"Unable to remove registry: {registry_uri}. "
            f"No registry store found in {config.xdg_ethpmcli_root}."
        )
    registry = resolve_uri_and_alias(registry_uri, alias, store_path)
    old_store_data = json.loads(store_path.read_text())
    updated_store_data = dissoc(old_store_data, registry.uri)
    write_store_data_to_disk(updated_store_data, store_path)


def activate_registry(uri_or_alias: str, config: Config) -> None:
    store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    store_data = json.loads(store_path.read_text())
    registry = resolve_uri_or_alias(uri_or_alias, store_path)
    active_registry_uri = get_active_registry(store_data)
    if registry.uri != active_registry_uri:
        deactivated_store_data = assoc_in(
            store_data, [active_registry_uri, "active"], False
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

    registries_and_aliases = get_all_registries_and_aliases(store_path)
    if alias:
        registry_uri = lookup_uri_by_alias(alias, registries_and_aliases)

    if not registry_uri or registry_uri not in registries_and_aliases.keys():
        raise InstallError(
            f"No registry @ {registry_uri} is available in {store_path}."
        )
    return StoredRegistry(registry_uri, False, alias, None)


def get_active_registry(store_data: Dict[URI, Any]) -> URI:
    for registry, data in store_data.items():
        if data["active"] is True:
            return registry
    raise InstallError("Invalid registry store data found.")


def lookup_uri_by_alias(alias: str, registries_and_aliases: Dict[URI, str]) -> URI:
    aliases_and_registries = {v: k for k, v in registries_and_aliases.items()}
    if alias not in aliases_and_registries:
        raise InstallError(
            f"Alias: {alias} not available. "
            f"Available aliases include: {list(aliases_and_registries.keys())}."
        )
    return aliases_and_registries[alias]


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
    all_registries = get_all_registries_and_aliases(store_path).keys()
    if registry_uri in all_registries:
        raise InstallError(f"Registry @ {registry_uri} already stored.")
    old_store_data = json.loads(store_path.read_text())
    new_registry_data = generate_registry_store_data(registry_uri, alias)
    updated_store_data = assoc(old_store_data, registry_uri, new_registry_data)
    write_store_data_to_disk(updated_store_data, store_path)


def get_all_registries_and_aliases(store_path: Path) -> Dict[URI, str]:
    store_data = json.loads(store_path.read_text())
    return {uri: store_data[uri]["alias"] for uri in store_data}


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

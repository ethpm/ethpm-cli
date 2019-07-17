import json
from pathlib import Path
import tempfile
from typing import Any, Dict, Iterable, Tuple, NamedTuple

from eth_typing import URI
from eth_utils import to_dict
from eth_utils.toolz import assoc, assoc_in, dissoc
from ethpm.backends.registry import parse_registry_uri, is_valid_registry_uri

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.config import Config
from ethpm_cli.constants import REGISTRY_STORE
from ethpm_cli.exceptions import InstallError

# todo:
# ethpm registry publish
# ethpm registry deploy
# ethpm registry remove
# store / list authorized registries


class StoredRegistry(NamedTuple):
    uri: URI
    active: bool = False
    alias: str = None
    ens: str = None

    @property
    def format_for_display(self) -> str:
        activated = "(active)" if self.active else ""
        return f"{self.uri} --- {self.alias} {activated}"


def list_registries(config: Config) -> None:
    registry_store = json.loads((config.ethpm_dir / REGISTRY_STORE).read_text())
    installed_registries = [
        StoredRegistry(reg, data["active"], data["alias"], data["ens"])
        for reg, data in registry_store.items()
    ]
    for registry in installed_registries:
        cli_logger.info(registry.format_for_display)


def add_registry(registry_uri: URI, alias: str, config: Config) -> None:
    store_path = config.ethpm_dir / REGISTRY_STORE
    if not store_path.is_file():
        generate_registry_store(registry_uri, alias, store_path)
    else:
        update_registry_store(registry_uri, alias, store_path)


def remove_registry(registry_uri: URI, alias: str, config: Config) -> None:
    store_path = config.ethpm_dir / REGISTRY_STORE
    if not store_path.is_file():
        raise InstallError(
            f"Unable to remove registry @ {registry_uri}. "
            f"No registry store found in {config.ethpm_dir}."
        )
    registry = resolve_uri_and_alias(registry_uri, alias, store_path)
    old_store_data = json.loads(store_path.read_text())
    updated_store_data = dissoc(old_store_data, registry.uri)
    write_store_data_to_disk(updated_store_data, store_path)


def activate_registry(uri_or_alias: str, config: Config) -> None:
    store_path = config.ethpm_dir / REGISTRY_STORE
    store_data = json.loads(store_path.read_text())
    registry = resolve_uri_or_alias(uri_or_alias, store_path)
    active_registry_uri = get_active_registry(store_data)
    if registry.uri == active_registry_uri:
        alias_msg = f" (alias: {registry.alias})" if registry.alias else " "
        raise InstallError(f"Registry @ {registry.uri}{alias_msg}, already activated.")
    deactivated_store_data = assoc_in(
        store_data, [active_registry_uri, "active"], False
    )
    activated_store_data = assoc_in(
        deactivated_store_data, [registry.uri, "active"], True
    )
    write_store_data_to_disk(activated_store_data, store_path)


def resolve_uri_or_alias(uri_or_alias: str, store_path: Path) -> StoredRegistry:
    if is_valid_registry_uri(uri_or_alias):
        return resolve_uri_and_alias(uri_or_alias, None, store_path)
    else:
        return resolve_uri_and_alias(None, uri_or_alias, store_path)


def resolve_uri_and_alias(registry_uri: URI, alias: str, store_path: Path) -> URI:
    if (registry_uri and alias) or (not registry_uri and not alias):
        raise InstallError("Cannot resolve both an alias and registry uri.")

    registries_and_aliases = get_all_registries_and_aliases(store_path)
    if alias:
        registry_uri = lookup_uri_by_alias(alias, registries_and_aliases)

    if registry_uri not in registries_and_aliases.keys():
        raise InstallError(
            f"No registry @ {registry_uri} is available in {store_path}."
        )
    return StoredRegistry(registry_uri, alias, None, None)


def get_active_registry(store_data: Dict[URI, Any]) -> URI:
    for registry, data in store_data.items():
        if data["active"] is True:
            return registry
    raise InstallError("Invalid registry store data found.")


def lookup_uri_by_alias(alias: str, registries_and_aliases: Dict[URI, str]) -> URI:
    aliases_and_registries = {v: k for k, v in registries_and_aliases.items()}
    if alias not in aliases_and_registries:
        raise InstallError(
            f"alias: {alias} not available. "
            f"Available aliases include: {list(aliases_and_registries.keys())}."
        )
    return aliases_and_registries[alias]


def generate_registry_store(registry_uri: URI, alias: str, store_path: Path) -> None:
    store_path.touch()
    init_registry_data = {
        registry_uri: generate_registry_store_data(registry_uri, alias, activate=True)
    }
    write_store_data_to_disk(init_registry_data, store_path)


def update_registry_store(registry_uri: URI, alias: str, store_path: Path) -> None:
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
    temp_store = Path(tempfile.NamedTemporaryFile().name)
    temp_store.write_text(json.dumps(store_data, indent=4, sort_keys=True))
    temp_store.replace(store_path)


@to_dict
def generate_registry_store_data(
    registry_uri: URI, alias: str, activate: bool = False
) -> Iterable[Tuple[str, Any]]:
    parsed_uri = parse_registry_uri(registry_uri)
    ens = None
    yield "ens", ens
    yield "address", parsed_uri.address
    yield "alias", alias
    yield "active", activate

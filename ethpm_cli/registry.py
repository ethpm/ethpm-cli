import json
from pathlib import Path
import tempfile
from typing import Any, Dict, Iterable, Tuple, NamedTuple
from collections import namedtuple

from eth_typing import URI
from eth_utils import to_dict
from eth_utils.toolz import assoc, assoc_in, dissoc
from ethpm.backends.registry import parse_registry_uri

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.config import Config
from ethpm_cli.constants import REGISTRY_STORE
from ethpm_cli.exceptions import InstallError

# todo:
# ethpm registry list
# ethpm registry publish
# ethpm registry deploy
# store / list authorized registries


class InstalledRegistry(NamedTuple):
    uri: URI
    active: bool
    alias: str
    ens: str

    @property
    def format_for_display(self) -> str:
        activated = "(active)" if self.active else ""
        return f"{self.uri} --- {self.alias} {activated}"


def list_registries(config: Config) -> None:
    registry_store = json.loads((config.ethpm_dir / REGISTRY_STORE).read_text())
    installed_registries = [InstalledRegistry(reg, data['active'], data['alias'], data['ens']) for reg, data in registry_store.items()]
    for registry in installed_registries:
        cli_logger.info(dir(registry))
        cli_logger.info(registry.format_for_display)



def add_registry(registry_uri: URI, alias: str, config: Config) -> None:
    store_path = config.ethpm_dir / REGISTRY_STORE
    if not store_path.is_file():
        store_path.touch()
        generate_registry_store(registry_uri, alias, store_path)
    else:
        update_registry_store(registry_uri, alias, store_path)


def remove_registry(registry_uri: URI, alias: str, config: Config) -> None:
    store_path = config.ethpm_dir / REGISTRY_STORE
    if not store_path.is_file():
        raise InstallError("no registry store")
    target_uri = resolve_uri_and_alias(registry_uri, alias, store_path)
    old_store_data = json.loads(store_path.read_text())
    updated_store_data = dissoc(old_store_data, target_uri)
    write_store_data_to_disk(updated_store_data, store_path)


def activate_registry(registry_uri: URI, alias: str, config: Config) -> None:
    store_path = config.ethpm_dir / REGISTRY_STORE
    target_uri = resolve_uri_and_alias(registry_uri, alias, store_path)
    store_data = json.loads(store_path.read_text())
    active_registry_uri = get_active_registry(store_data)
    if target_uri == active_registry_uri:
        raise InstallError
    deactivated_store_data = assoc_in(
        store_data, [active_registry_uri, "active"], False
    )
    activated_store_data = assoc_in(
        deactivated_store_data, [target_uri, "active"], True
    )
    write_store_data_to_disk(activated_store_data, store_path)


def resolve_uri_and_alias(registry_uri: URI, alias: str, store_path: Path) -> URI:
    if registry_uri and alias:
        raise InstallError

    registries_and_aliases = get_all_registries_and_aliases(store_path)
    if alias:
        if registry_uri:
            raise InstallError()
        registry_uri = lookup_uri_by_alias(alias, registries_and_aliases)

    if registry_uri not in registries_and_aliases.keys():
        raise InstallError("xxx")
    return registry_uri


def get_active_registry(store_data: Dict[URI, Any]) -> URI:
    for registry, data in store_data.items():
        if data["active"] is True:
            return registry
    raise Exception


def lookup_uri_by_alias(alias: str, registries_and_aliases: Dict[URI, str]) -> URI:
    aliases_and_registries = {v: k for k, v in registries_and_aliases.items()}
    if alias not in aliases_and_registries:
        raise InstallError()
    return aliases_and_registries[alias]


def generate_registry_store(registry_uri: URI, alias: str, store_path: Path) -> None:
    init_registry_data = {
        registry_uri: generate_registry_store_data(registry_uri, alias, activate=True)
    }
    write_store_data_to_disk(init_registry_data, store_path)


def update_registry_store(registry_uri: URI, alias: str, store_path: Path) -> None:
    all_registries = get_all_registries_and_aliases(store_path).keys()
    if registry_uri in all_registries:
        raise InstallError("already added")
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

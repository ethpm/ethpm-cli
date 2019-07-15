from eth_utils import to_dict
from ethpm_cli.exceptions import InstallError
from eth_utils.toolz import assoc, dissoc
from pathlib import Path
import tempfile
from ethpm_cli.constants import REGISTRY_STORE
import json
from ethpm.backends.registry import parse_registry_uri
# ethpm registry add erc1319://0x123/1/ --alias
# ethpm registry remove
# ethpm registry set-active
# ethpm registry list
# ethpm registry publish
# ethpm registry create


# registry address
# chain id
# ens name
# owner
# active?




# ethpm registry add erc1319://0x123:1
def add_registry(registry_uri, alias, config):
    store_path = config.ethpm_dir / REGISTRY_STORE
    if not store_path.is_file():
        store_path.touch()
        generate_registry_store(registry_uri, alias, store_path)
    else:
        update_registry_store(registry_uri, alias, store_path)


# expects registry_uri or alias
def remove_registry(registry_uri, alias, config):
    store_path = config.ethpm_dir / REGISTRY_STORE
    if not store_path.is_file():
        raise InstallError("no registry store")
    registries_and_aliases = get_all_registries_and_aliases(store_path)
    if registry_uri and alias:
        raise InstallError

    if alias:
        if registry_uri:
            raise InstallError()
        registry_uri = lookup_uri_by_alias(alias, registries_and_aliases)

    if registry_uri not in registries_and_aliases.keys():
        raise InstallError("xxx")
    old_store_data = json.loads(store_path.read_text())
    updated_store_data = dissoc(old_store_data, registry_uri)
    write_store_data_to_disk(updated_store_data, store_path)

def lookup_uri_by_alias(alias, registries_and_aliases):
    aliases_and_registries = {v: k for k, v in registries_and_aliases.items()}
    if alias not in aliases_and_registries:
        raise InstallError()
    return aliases_and_registries[alias]

def generate_registry_store(registry_uri, alias, store_path):
    init_registry_data = {registry_uri: generate_registry_store_data(registry_uri, alias)}
    write_store_data_to_disk(init_registry_data, store_path)


def update_registry_store(registry_uri, alias, store_path):
    all_registries = get_all_registries_and_aliases(store_path).keys()
    if registry_uri in all_registries:
        raise InstallError("already added")
    old_store_data = json.loads(store_path.read_text())
    new_registry_data = generate_registry_store_data(registry_uri, alias)
    updated_store_data = assoc(old_store_data, registry_uri, new_registry_data)
    write_store_data_to_disk(updated_store_data, store_path)


def get_all_registries_and_aliases(store_path):
    store_data = json.loads(store_path.read_text())
    return {uri: store_data[uri]['alias'] for uri in store_data}


def write_store_data_to_disk(store_data, store_path):
    temp_store = Path(tempfile.NamedTemporaryFile().name)
    temp_store.write_text(json.dumps(store_data, indent=4, sort_keys=True))
    temp_store.replace(store_path)


def activate_registry():
    pass


@to_dict
def generate_registry_store_data(registry_uri, alias):
    parsed_uri = parse_registry_uri(registry_uri)
    ens = None
    yield "ens", ens
    yield "address", parsed_uri.address
    yield "alias", alias
    yield "active", False

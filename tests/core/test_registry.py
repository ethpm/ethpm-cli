import pytest
from ethpm_cli.exceptions import InstallError
import json
from ethpm_cli.registry import generate_registry_store_data, add_registry, remove_registry
from ethpm_cli.constants import REGISTRY_STORE


@pytest.mark.parametrize(
    "uri,alias,expected",
    (
        (
            "erc1319://0x1230000000000000000000000000000000000000:1",
            "home",
            {
                "address": "0x1230000000000000000000000000000000000000",
                "alias": "home",
                "ens": None,
                "active": False,
            }),
    )
)
def test_generate_registry_store_data(uri, alias, expected):
    actual = generate_registry_store_data(uri, alias)
    assert actual == expected


def test_add_registry(config, test_assets_dir):
    expected_registry_store = json.loads((test_assets_dir / 'registry_store' / 'init.json').read_text())
    add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)
    actual_registry_store = json.loads((config.ethpm_dir / REGISTRY_STORE).read_text())
    assert actual_registry_store == expected_registry_store


def test_add_multiple_registries(config, test_assets_dir):
    expected_registry_store = json.loads((test_assets_dir / 'registry_store' / 'multiple.json').read_text())
    add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)
    add_registry("erc1319://0xabc0000000000000000000000000000000000000:1", 'other', config)
    actual_registry_store = json.loads((config.ethpm_dir / REGISTRY_STORE).read_text())
    assert actual_registry_store == expected_registry_store


def test_adding_an_existing_registry_raises_exception(config):
    add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)
    with pytest.raises(InstallError, match='already added'):
        add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)


def test_remove_registry(config, test_assets_dir):
    add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)
    add_registry("erc1319://0xabc0000000000000000000000000000000000000:1", 'other', config)
    remove_registry("erc1319://0xabc0000000000000000000000000000000000000:1", None, config)
    expected_registry_store = json.loads((test_assets_dir / 'registry_store' / 'init.json').read_text())
    actual_registry_store = json.loads((config.ethpm_dir / REGISTRY_STORE).read_text())
    assert actual_registry_store == expected_registry_store


def test_remove_registry_with_nonexisting_store(config):
    with pytest.raises(InstallError, match="no registry store"):
        remove_registry("erc1319://0xabc0000000000000000000000000000000000000:1", None, config)

def test_remove_aliased_registry(test_assets_dir, config):
    add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)
    add_registry("erc1319://0xabc0000000000000000000000000000000000000:1", 'other', config)
    remove_registry(None, "other", config)
    expected_registry_store = json.loads((test_assets_dir / 'registry_store' / 'init.json').read_text())
    actual_registry_store = json.loads((config.ethpm_dir / REGISTRY_STORE).read_text())
    assert actual_registry_store == expected_registry_store


def test_remove_nonexisting_registry_raises_exception(config):
    add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)
    with pytest.raises(InstallError):
        remove_registry("erc1319://0xabc0000000000000000000000000000000000000:1", None, config)

def test_remove_nonexisting_aliased_registry_raises_exception(config):
    add_registry("erc1319://0x1230000000000000000000000000000000000000:1", 'mine', config)
    with pytest.raises(InstallError):
        remove_registry(None, 'other', config)

def test_remove_registry_expects_uri_or_alias(config):
    with pytest.raises(InstallError):
        remove_registry(None, None, config)
    with pytest.raises(InstallError):
        remove_registry("erc1319://0xabc0000000000000000000000000000000000000:1", "mine", config)


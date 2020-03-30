import json

import pytest

from ethpm_cli.commands.registry import (
    activate_registry,
    add_registry,
    generate_registry_store_data,
    remove_registry,
    resolve_uri_or_alias,
)
from ethpm_cli.constants import REGISTRY_STORE
from ethpm_cli.exceptions import InstallError

URI_1 = "erc1319://0x1230000000000000000000000000000000000000:1"
URI_2 = "erc1319://0xabc0000000000000000000000000000000000000:1"


@pytest.mark.parametrize(
    "uri,alias,expected",
    (
        (
            URI_1,
            "home",
            {
                "address": "0x1230000000000000000000000000000000000000",
                "alias": "home",
                "ens": None,
                "active": False,
            },
        ),
    ),
)
def test_generate_registry_store_data(uri, alias, expected):
    actual = generate_registry_store_data(uri, alias)
    assert actual == expected


def test_add_registry(config, test_assets_dir):
    expected_registry_store = json.loads(
        (test_assets_dir / "registry_store" / "init.json").read_text()
    )
    add_registry(URI_1, "mine", config)
    actual_registry_store = json.loads(
        (config.xdg_ethpmcli_root / REGISTRY_STORE).read_text()
    )
    assert actual_registry_store == expected_registry_store


def test_add_multiple_registries(config, test_assets_dir):
    expected_registry_store = json.loads(
        (test_assets_dir / "registry_store" / "multiple.json").read_text()
    )
    add_registry(URI_1, "mine", config)
    add_registry(URI_2, "other", config)
    actual_registry_store = json.loads(
        (config.xdg_ethpmcli_root / REGISTRY_STORE).read_text()
    )
    assert actual_registry_store == expected_registry_store


def test_adding_an_existing_registry_raises_exception(config):
    add_registry(URI_1, "mine", config)
    with pytest.raises(InstallError, match="already stored."):
        add_registry(URI_1, "mine", config)


def test_remove_registry(config, test_assets_dir):
    add_registry(URI_1, "mine", config)
    add_registry(URI_2, "other", config)
    remove_registry(URI_2, config)
    expected_registry_store = json.loads(
        (test_assets_dir / "registry_store" / "init.json").read_text()
    )
    actual_registry_store = json.loads(
        (config.xdg_ethpmcli_root / REGISTRY_STORE).read_text()
    )
    assert actual_registry_store == expected_registry_store


def test_remove_registry_with_nonexisting_store(config):
    with pytest.raises(InstallError, match="Unable to remove registry"):
        remove_registry(URI_2, config)


def test_remove_aliased_registry(test_assets_dir, config):
    add_registry(URI_1, "mine", config)
    add_registry(URI_2, "other", config)
    remove_registry("other", config)
    expected_registry_store = json.loads(
        (test_assets_dir / "registry_store" / "init.json").read_text()
    )
    actual_registry_store = json.loads(
        (config.xdg_ethpmcli_root / REGISTRY_STORE).read_text()
    )
    assert actual_registry_store == expected_registry_store


def test_remove_nonexisting_registry_raises_exception(config):
    add_registry(URI_1, "mine", config)
    with pytest.raises(InstallError):
        remove_registry(URI_2, config)


def test_remove_nonexisting_aliased_registry_raises_exception(config):
    add_registry(URI_1, "mine", config)
    with pytest.raises(InstallError):
        remove_registry("other", config)


def test_remove_active_registry_raises_error(config):
    add_registry(URI_1, "mine", config)
    with pytest.raises(InstallError):
        remove_registry(URI_2, config)


def test_activate_different_registry(test_assets_dir, config):
    add_registry(URI_1, "mine", config)
    add_registry(URI_2, "other", config)
    activate_registry(URI_2, config)
    store_data = json.loads((config.xdg_ethpmcli_root / REGISTRY_STORE).read_text())
    assert store_data[URI_2]["active"] is True
    assert store_data[URI_1]["active"] is False


def test_activate_aliased_registry(test_assets_dir, config):
    add_registry(URI_1, "mine", config)
    add_registry(URI_2, "other", config)
    activate_registry("other", config)
    store_data = json.loads((config.xdg_ethpmcli_root / REGISTRY_STORE).read_text())
    assert store_data[URI_2]["active"] is True
    assert store_data[URI_1]["active"] is False


def test_unable_to_activate_nonexistent_registry(config):
    add_registry(URI_1, "mine", config)
    with pytest.raises(InstallError):
        activate_registry(URI_2, config)


def test_unable_to_activate_nonexistent_aliased_registry(config):
    add_registry(URI_1, "mine", config)
    with pytest.raises(InstallError):
        activate_registry("other", config)


@pytest.mark.parametrize(
    "uri,alias,expected",
    (
        (
            URI_1,
            "home",
            {
                "uri": "erc1319://0x1230000000000000000000000000000000000000:1",
                "alias": "home",
            },
        ),
        (
            URI_2,
            "owned",
            {
                "uri": "erc1319://0xabc0000000000000000000000000000000000000:1",
                "alias": "owned",
            },
        ),
    ),
)
def test_resolve_uri_or_alias(config, uri, alias, expected):
    store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    add_registry(uri, alias, config)
    registry = resolve_uri_or_alias(alias, store_path)
    assert registry.alias == expected["alias"]
    registry = resolve_uri_or_alias(uri, store_path)
    assert registry.uri == expected["uri"]


@pytest.mark.parametrize(
    "uri,alias", ((URI_1, "home",), (URI_2, "owned",),),
)
def test_resolve_uri_or_alias_raises_install_error(config, uri, alias):
    store_path = config.xdg_ethpmcli_root / REGISTRY_STORE
    add_registry(uri, alias, config)
    with pytest.raises(InstallError):
        resolve_uri_or_alias("other", store_path)
    with pytest.raises(InstallError):
        resolve_uri_or_alias("foo://", store_path)

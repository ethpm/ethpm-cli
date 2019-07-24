from argparse import Namespace
import logging
from pathlib import Path

import pytest

from ethpm_cli._utils.testing import check_dir_trees_equal
from ethpm_cli.constants import ETHPM_DIR_NAME
from ethpm_cli.exceptions import InstallError
from ethpm_cli.install import (
    Config,
    install_package,
    list_installed_packages,
    uninstall_package,
)
from ethpm_cli.package import Package


@pytest.fixture
def owned_pkg(config):
    return Package(
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
        None,
        config.ipfs_backend,
    )


@pytest.fixture
def wallet_pkg(config):
    return Package(
        "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
        None,
        config.ipfs_backend,
    )


@pytest.mark.parametrize(
    "uri,pkg_name,alias,install_type",
    (
        (
            "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            "owned",
            None,
            "ipfs_uri",
        ),
        (
            "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            "owned",
            "owned-alias",
            "ipfs_uri_alias",
        ),
        (
            "erc1319://0x6b5DA3cA4286Baa7fBaf64EEEE1834C7d430B729:1/owned?version=1.0.0",
            "owned",
            None,
            "registry_uri",
        ),
        (
            "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
            "wallet",
            None,
            "ipfs_uri",
        ),
    ),
)
def test_install_package(uri, pkg_name, alias, install_type, config, test_assets_dir):
    pkg = Package(uri, alias, config.ipfs_backend)
    install_package(pkg, config)

    expected_package = test_assets_dir / pkg_name / install_type / ETHPM_DIR_NAME
    assert check_dir_trees_equal(config.ethpm_dir, expected_package)


def test_cannot_install_same_package_twice(config, owned_pkg):
    install_package(owned_pkg, config)

    with pytest.raises(InstallError, match="Installation conflict:"):
        install_package(owned_pkg, config)


def test_can_install_same_package_twice_if_aliased(config, owned_pkg, test_assets_dir):
    aliased_pkg = Package(
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
        "owned-alias",
        config.ipfs_backend,
    )
    install_package(owned_pkg, config)
    install_package(aliased_pkg, config)

    assert (config.ethpm_dir / "owned").is_dir()
    assert check_dir_trees_equal(
        config.ethpm_dir / "owned",
        test_assets_dir / "owned" / "ipfs_uri" / ETHPM_DIR_NAME / "owned",
    )
    assert (config.ethpm_dir / "owned-alias").is_dir()
    assert check_dir_trees_equal(
        config.ethpm_dir / "owned-alias",
        test_assets_dir / "owned" / "ipfs_uri_alias" / ETHPM_DIR_NAME / "owned-alias",
    )


def test_install_multiple_packages(config, test_assets_dir, owned_pkg, wallet_pkg):
    install_package(owned_pkg, config)
    install_package(wallet_pkg, config)

    assert (config.ethpm_dir / "wallet").is_dir()
    assert (config.ethpm_dir / "owned").is_dir()
    assert check_dir_trees_equal(
        config.ethpm_dir, (test_assets_dir / "multiple" / ETHPM_DIR_NAME)
    )


@pytest.mark.parametrize("uninstall,keep", (("wallet", "owned"), ("owned", "wallet")))
def test_uninstall_packages(
    uninstall, keep, config, test_assets_dir, owned_pkg, wallet_pkg
):
    install_package(owned_pkg, config)
    install_package(wallet_pkg, config)
    uninstall_package(uninstall, config)

    assert (config.ethpm_dir / keep).is_dir()
    assert not (config.ethpm_dir / uninstall).is_dir()
    assert check_dir_trees_equal(
        config.ethpm_dir, (test_assets_dir / keep / "ipfs_uri" / ETHPM_DIR_NAME)
    )


def test_uninstall_package_warns_if_package_doesnt_exist(config):
    with pytest.raises(InstallError, match="No package with the name invalid"):
        uninstall_package("invalid", config)


def test_list(config, owned_pkg, wallet_pkg, caplog):
    install_package(owned_pkg, config)
    install_package(wallet_pkg, config)

    with caplog.at_level(logging.INFO):
        list_installed_packages(config)
        assert (
            "owned==1.0.0 --- (ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW)\n"
            in caplog.text
        )  # noqa: E501
        assert (
            "wallet==1.0.0 --- (ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1)\n"
            in caplog.text
        )  # noqa: E501
        assert (
            "- safe-math-lib==1.0.0 --- (ipfs://QmWgvM8yXGyHoGWqLFXvareJsoCZVsdrpKNCLMun3RaSJm)\n"
            in caplog.text
        )  # noqa: E501
        assert (
            "- owned==1.0.0 --- (ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW)\n"
            in caplog.text
        )  # noqa: E501

from argparse import Namespace
import logging

import pytest

from ethpm_cli._utils.filesystem import check_dir_trees_equal
from ethpm_cli.commands.install import (
    install_package,
    list_installed_packages,
    uninstall_package,
)
from ethpm_cli.commands.package import Package
from ethpm_cli.constants import ETHPM_PACKAGES_DIR
from ethpm_cli.exceptions import InstallError


@pytest.fixture
def owned_pkg(config):
    args = Namespace(uri="ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW")
    return Package(args, config.ipfs_backend)


@pytest.fixture
def wallet_pkg(config):
    args = Namespace(uri="ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1")
    return Package(args, config.ipfs_backend)


@pytest.mark.parametrize(
    "args,pkg_name,install_type",
    (
        (
            Namespace(uri="ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW"),
            "owned",
            "ipfs_uri",
        ),
        (
            Namespace(
                uri="ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
                alias="owned-alias",
            ),
            "owned",
            "ipfs_uri_alias",
        ),
        (
            Namespace(
                uri="erc1319://0x1457890158DECD360e6d4d979edBcDD59c35feeB:1/owned@1.0.0"
            ),
            "owned",
            "registry_uri",
        ),
        (
            Namespace(uri="ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1"),
            "wallet",
            "ipfs_uri",
        ),
    ),
)
def test_install_package(args, pkg_name, install_type, config, test_assets_dir):
    pkg = Package(args, config.ipfs_backend)
    install_package(pkg, config)

    expected_package = test_assets_dir / pkg_name / install_type / ETHPM_PACKAGES_DIR
    assert check_dir_trees_equal(config.ethpm_dir, expected_package)


def test_install_package_with_ens_in_registry_uri(config):
    uri = Namespace(uri="erc1319://ens.snakecharmers.eth:1/ens@1.0.0")
    pkg = Package(uri, config.ipfs_backend)
    install_package(pkg, config)

    assert (config.ethpm_dir).is_dir()
    assert (config.ethpm_dir / "ens").is_dir()
    assert (config.ethpm_dir / "ens" / "_src" / "ENS.sol").is_file()


def test_cannot_install_same_package_twice(config, owned_pkg):
    install_package(owned_pkg, config)

    with pytest.raises(InstallError, match="Installation conflict:"):
        install_package(owned_pkg, config)


def test_can_install_same_package_twice_if_aliased(config, owned_pkg, test_assets_dir):
    aliased_pkg = Package(
        Namespace(
            uri="ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            alias="owned-alias",
        ),
        config.ipfs_backend,
    )
    install_package(owned_pkg, config)
    install_package(aliased_pkg, config)

    assert (config.ethpm_dir / "owned").is_dir()
    assert check_dir_trees_equal(
        config.ethpm_dir / "owned",
        test_assets_dir / "owned" / "ipfs_uri" / ETHPM_PACKAGES_DIR / "owned",
    )
    assert (config.ethpm_dir / "owned-alias").is_dir()
    assert check_dir_trees_equal(
        config.ethpm_dir / "owned-alias",
        test_assets_dir
        / "owned"  # noqa: W503
        / "ipfs_uri_alias"  # noqa: W503
        / ETHPM_PACKAGES_DIR  # noqa: W503
        / "owned-alias",  # noqa: W503
    )


def test_install_multiple_packages(config, test_assets_dir, owned_pkg, wallet_pkg):
    install_package(owned_pkg, config)
    install_package(wallet_pkg, config)

    assert (config.ethpm_dir / "wallet").is_dir()
    assert (config.ethpm_dir / "owned").is_dir()
    assert check_dir_trees_equal(
        config.ethpm_dir, (test_assets_dir / "multiple" / ETHPM_PACKAGES_DIR)
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
        config.ethpm_dir, (test_assets_dir / keep / "ipfs_uri" / ETHPM_PACKAGES_DIR)
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

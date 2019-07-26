from argparse import Namespace
from pathlib import Path

import pytest

from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.config import Config
from ethpm_cli.constants import (
    ETHPM_DIR_ENV_VAR,
    ETHPM_PACKAGES_DIR,
    IPFS_CHAIN_DATA,
    KEYFILE_PATH,
)


@pytest.fixture
def namespace():
    namespace = Namespace()
    namespace.local_ipfs = False
    namespace.install_uri = None
    namespace.alias = None
    return namespace


def test_config_with_cli_ethpm_dir(tmpdir, namespace):
    ethpm_dir = Path(tmpdir) / ETHPM_PACKAGES_DIR
    namespace.ethpm_dir = ethpm_dir
    config = Config(namespace)
    assert config.ethpm_dir == ethpm_dir


def test_config_without_cli_ethpm_dir(namespace):
    namespace.ethpm_dir = None
    config = Config(namespace)
    assert config.ethpm_dir.is_dir()
    assert config.ethpm_dir.name == ETHPM_PACKAGES_DIR


def test_config_with_ethpm_dir_env_var(tmpdir, namespace, monkeypatch):
    ethpm_dir = Path(tmpdir) / ETHPM_PACKAGES_DIR
    monkeypatch.setenv(ETHPM_DIR_ENV_VAR, str(ethpm_dir))
    namespace.ethpm_dir = None
    config = Config(namespace)
    assert config.ethpm_dir == ethpm_dir
    assert isinstance(config.ethpm_dir, Path)


def test_config_with_cli_ethpm_dir_overrides_env_var(tmpdir, namespace, monkeypatch):
    env_dir = Path(tmpdir) / "env"
    cli_dir = Path(tmpdir) / "cli"
    env_dir.mkdir()
    cli_dir.mkdir()
    ethpm_dir_env = env_dir / ETHPM_PACKAGES_DIR
    ethpm_dir_cli = cli_dir / ETHPM_PACKAGES_DIR
    ethpm_dir_env.mkdir()
    ethpm_dir_cli.mkdir()
    monkeypatch.setenv(ETHPM_DIR_ENV_VAR, str(ethpm_dir_env))
    namespace.ethpm_dir = ethpm_dir_cli
    config = Config(namespace)
    assert config.ethpm_dir == ethpm_dir_cli


@pytest.mark.parametrize(
    "chain_id,expected",
    ((None, "1"), (1, "1"), (3, "3"), (4, "4"), (5, "5"), (42, "42")),
)
def test_config_initializes_with_correct_w3_instance(namespace, chain_id, expected):
    namespace.chain_id = chain_id
    config = Config(namespace)
    assert config.w3.net.version == expected


def test_config_with_unsupported_chain_id_raises_exception(namespace):
    namespace.chain_id = 2
    with pytest.raises(Exception):
        Config(namespace)


def test_config_initializes_xdg_dir(config):
    xdg_ethpm_dir = get_xdg_ethpmcli_root()
    assert (xdg_ethpm_dir / KEYFILE_PATH).is_file()
    assert (xdg_ethpm_dir / IPFS_CHAIN_DATA).is_file()

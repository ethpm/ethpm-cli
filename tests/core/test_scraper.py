import json
import os
from pathlib import Path

from ethpm import Package
import pytest
from pytest_ethereum.deployer import Deployer
from web3 import Web3

from ethpm_cli import CLI_ASSETS_DIR
from ethpm_cli._utils.testing import check_dir_trees_equal
from ethpm_cli.scraper import scrape


@pytest.fixture
def w3():
    return Web3(Web3.EthereumTesterProvider())


@pytest.fixture
def log_deployer(w3):
    pkg = Package(json.loads((CLI_ASSETS_DIR / "1.0.1.json").read_text()), w3)
    return Deployer(pkg)


@pytest.fixture
def log(log_deployer, tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    monkeypatch.setenv("XDG_ETHPMCLI_ROOT", str(Path(tmpdir / "ethpmcli_dir")))
    return log_deployer.deploy("Log").deployments.get_instance("Log")


def release(log, w3, name, version, uri):
    tx_hash = log.functions.release(name, version, uri).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)


def test_scraper_writes_to_disk(log, test_assets_dir, w3):
    release(
        log,
        w3,
        "owned",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )

    w3.testing.mine(3)
    release(
        log,
        w3,
        "owned-dupe",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )

    w3.testing.mine(3)
    release(
        log,
        w3,
        "wallet",
        "1.0.0",
        "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
    )
    ethpmcli_dir = Path(os.environ["XDG_ETHPMCLI_ROOT"])
    scrape(w3, ethpmcli_dir)
    assert check_dir_trees_equal(ethpmcli_dir, (test_assets_dir.parent / "ipfs_assets"))


def test_scraper_imports_existing_ethpmcli_dir(log, test_assets_dir, w3):
    release(
        log,
        w3,
        "owned",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )

    w3.testing.mine(3)
    release(
        log,
        w3,
        "owned-dupe",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )

    ethpmcli_dir = Path(os.environ["XDG_ETHPMCLI_ROOT"])
    scrape(w3, ethpmcli_dir)
    w3.testing.mine(3)
    release(
        log,
        w3,
        "wallet",
        "1.0.0",
        "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
    )

    scrape(w3, ethpmcli_dir)
    assert check_dir_trees_equal(ethpmcli_dir, (test_assets_dir.parent / "ipfs_assets"))

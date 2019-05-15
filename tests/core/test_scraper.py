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


@pytest.fixture
def log_2(log_deployer):
    return log_deployer.deploy("Log").deployments.get_instance("Log")


def release(log, w3, name, version, uri):
    tx_hash = log.functions.release(name, version, uri).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)


def test_scraper_logs_scraped_block_ranges(log, w3):
    ethpmcli_dir = Path(os.environ["XDG_ETHPMCLI_ROOT"])

    # Initial scrape
    w3.testing.mine(6)
    scrape(w3, ethpmcli_dir, 1)
    expected_1 = {"chain_id": "0x3d", "scraped_blocks": [{"min": "0", "max": "6"}]}
    actual_1 = json.loads((ethpmcli_dir / "chain_data.json").read_text())
    assert actual_1 == expected_1

    # Scrape from custom start block
    w3.testing.mine(4)
    scrape(w3, ethpmcli_dir, 9)
    expected_2 = {
        "chain_id": "0x3d",
        "scraped_blocks": [{"min": "0", "max": "6"}, {"min": "9", "max": "10"}],
    }
    actual_2 = json.loads((ethpmcli_dir / "chain_data.json").read_text())
    assert actual_2 == expected_2

    # Complex scrape from custom start block
    w3.testing.mine(4)
    expected_3 = {
        "chain_id": "0x3d",
        "scraped_blocks": [
            {"min": "0", "max": "6"},
            {"min": "9", "max": "10"},
            {"min": "13", "max": "14"},
        ],
    }
    scrape(w3, ethpmcli_dir, 13)
    actual_3 = json.loads((ethpmcli_dir / "chain_data.json").read_text())
    assert actual_3 == expected_3

    # Test ranges partially collapse
    scrape(w3, ethpmcli_dir, 10)
    expected_4 = {
        "chain_id": "0x3d",
        "scraped_blocks": [{"min": "0", "max": "6"}, {"min": "9", "max": "14"}],
    }
    actual_4 = json.loads((ethpmcli_dir / "chain_data.json").read_text())
    assert actual_4 == expected_4

    # Test ranges fully collapse
    scrape(w3, ethpmcli_dir, 1)
    expected_5 = {"chain_id": "0x3d", "scraped_blocks": [{"min": "0", "max": "14"}]}
    actual_5 = json.loads((ethpmcli_dir / "chain_data.json").read_text())
    assert actual_5 == expected_5


def test_scraper_writes_to_disk(log, log_2, test_assets_dir, w3):
    release(
        log,
        w3,
        "owned",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )

    w3.testing.mine(3)
    release(
        log_2,
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

    w3.testing.mine(3)
    ethpmcli_dir = Path(os.environ["XDG_ETHPMCLI_ROOT"])
    scrape(w3, ethpmcli_dir, 1)
    assert check_dir_trees_equal(ethpmcli_dir, (test_assets_dir.parent / "ipfs"))


def test_scraper_imports_existing_ethpmcli_dir(log, log_2, test_assets_dir, w3):
    release(
        log,
        w3,
        "owned",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )

    w3.testing.mine(3)
    release(
        log_2,
        w3,
        "owned-dupe",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )

    ethpmcli_dir = Path(os.environ["XDG_ETHPMCLI_ROOT"])
    # First scrape
    scrape(w3, ethpmcli_dir, 1)
    w3.testing.mine(3)
    release(
        log,
        w3,
        "wallet",
        "1.0.0",
        "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
    )
    w3.testing.mine(3)
    # Second scrape
    scrape(w3, ethpmcli_dir, 1)
    assert check_dir_trees_equal(ethpmcli_dir, (test_assets_dir.parent / "ipfs"))

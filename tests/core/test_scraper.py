import json
import logging
from pathlib import Path

from ethpm import Package
import pytest
from pytest_ethereum.deployer import Deployer
from web3 import Web3

from ethpm_cli import CLI_ASSETS_DIR
from ethpm_cli._utils.testing import check_dir_trees_equal
from ethpm_cli.scraper import Scraper


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
    return log_deployer.deploy("Log").deployments.get_instance("Log")


@pytest.fixture
def scraper(w3):
    return Scraper(w3, ws_w3=w3, logger=logging.getLogger())


def release(log, w3, name, version, uri):
    tx_hash = log.functions.release(name, version, uri).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)


def test_scraper_scrapes_w3_for_version_release_events(log_deployer, log, w3, scraper):
    assert scraper.process_available_blocks() == {}
    assert scraper.version_release_data == {}

    log_2 = log_deployer.deploy("Log").deployments.get_instance("Log")
    release(
        log,
        w3,
        "owned",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )
    release(
        log_2,
        w3,
        "wallet",
        "2",
        "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
    )

    new_entries = scraper.process_available_blocks()
    assert len(new_entries) == 2
    assert scraper.last_processed_block == w3.eth.blockNumber
    assert scraper.version_release_data == {
        "3": {
            log.address: {
                "packageName": "owned",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            }
        },
        "4": {
            log_2.address: {
                "packageName": "wallet",
                "version": "2",
                "manifestURI": "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
            }
        },
    }

    release(log_2, w3, "pkg", "1.0.0", "www.google.com")
    # invalid release
    tx_hash = log_2.functions.invalid("other", "2", "www.google.com").transact()
    w3.eth.waitForTransactionReceipt(tx_hash)

    assert len(scraper.process_available_blocks()) == 3
    assert scraper.version_release_data == {
        "3": {
            log.address: {
                "packageName": "owned",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            }
        },
        "4": {
            log_2.address: {
                "packageName": "wallet",
                "version": "2",
                "manifestURI": "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
            }
        },
        "5": {
            log_2.address: {
                "packageName": "pkg",
                "version": "1.0.0",
                "manifestURI": "www.google.com",
            }
        },
    }


def test_scraper_resolves_nested_uris_and_dependencies(log, w3, scraper):
    release(
        log,
        w3,
        "owned",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )
    # wallet pkg has build_dependencies
    release(
        log,
        w3,
        "wallet",
        "1.0.0",
        "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
    )

    scraper.process_available_blocks()
    assert scraper.version_release_data == {
        "2": {
            log.address: {
                "packageName": "owned",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            }
        },
        "3": {
            log.address: {
                "packageName": "wallet",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
            }
        },
    }
    # Expect a total of 7 ipfs uris after resolving all build dependencies
    assert len(scraper.ipfs_uris) == 7


def test_scraper_resolves_nested_uris_with_github_uris(log, w3, scraper):
    release(
        log,
        w3,
        "owned",
        "1.0.0",
        "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
    )
    release(
        log,
        w3,
        "wallet",
        "1.0.0",
        "https://api.github.com/repos/ethpm/ethpm-spec/git/blobs/02e437d45b5dd19e1564da416afed439a5324cca",  # noqa: E501
    )

    scraper.process_available_blocks()
    assert len(scraper.ipfs_uris) == 6


def test_scraper_writes_to_disk(log, test_assets_dir, w3, scraper):
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

    scraper.process_available_blocks()
    assert check_dir_trees_equal(
        scraper.content_dir, (test_assets_dir.parent / "ipfs_assets")
    )


def test_scraper_imports_existing_content_dir(
    log, tmpdir, test_assets_dir, w3, scraper
):
    ipfs_assets_dir = Path(tmpdir) / "ipfs_assets"

    # ADD CASE FROM OTHER CONTRACT ADDRESS
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

    scraper.process_available_blocks()

    w3.testing.mine(3)
    release(
        log,
        w3,
        "wallet",
        "1.0.0",
        "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
    )

    scraper_2 = Scraper(w3, w3, ipfs_assets_dir, logger=logging.getLogger())
    scraper_2.process_available_blocks()
    print((scraper_2.content_dir / "event_data.json").read_text())
    print("----")
    print((test_assets_dir.parent / "ipfs_assets" / "event_data.json").read_text())
    assert check_dir_trees_equal(
        scraper_2.content_dir, (test_assets_dir.parent / "ipfs_assets")
    )

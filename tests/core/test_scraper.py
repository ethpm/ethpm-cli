from pytest_ethereum.deployer import Deployer
from ethpm_cli._utils.testing import check_dir_trees_equal
from ethpm import Package
import pytest
from web3 import Web3
from pathlib import Path
import json

from ethpm_cli.scraper import Scraper

ASSETS_DIR = Path(__file__).parent.parent.parent / "ethpm_cli" / "assets"
TEST_ASSETS = Path(__file__).parent / "ipfs_assets"


@pytest.fixture
def w3():
    return Web3(Web3.EthereumTesterProvider())


@pytest.fixture
def log_deployer(w3):
    pkg = Package(json.loads((ASSETS_DIR / "1.0.1.json").read_text()), w3)
    return Deployer(pkg)


@pytest.fixture
def log_pkg(log_deployer, tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    return log_deployer.deploy("Log")


def test_scraper_scrapes_w3_for_emitted_version_release_events(
    log_deployer, log_pkg, w3
):
    log = log_pkg.deployments.get_instance("Log")
    log_2 = log_deployer.deploy("Log").deployments.get_instance("Log")
    scraper = Scraper(w3, w3)
    assert scraper.process_available_blocks() == {}
    assert scraper.emitted_version_data == {}

    tx_hash = log.functions.release(
        "owned", "1.0.0", "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)
    tx_hash_2 = log_2.functions.release("other", "2", "github.com").transact()
    w3.eth.waitForTransactionReceipt(tx_hash_2)
    new_entries = scraper.process_available_blocks()
    assert len(new_entries) == 2
    assert scraper.last_processed_block == w3.eth.blockNumber
    assert scraper.emitted_version_data == {
        3: {
            log.address: {
                "packageName": "owned",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            }
        },
        4: {
            log_2.address: {
                "packageName": "other",
                "version": "2",
                "manifestURI": "github.com",
            }
        },
    }

    tx_hash_3 = log_2.functions.release("pkg", "1.0.0", "www.google.com").transact()
    w3.eth.waitForTransactionReceipt(tx_hash_3)
    tx_hash_4 = log_2.functions.invalid("other", "3", "www.yahoo.com").transact()
    w3.eth.waitForTransactionReceipt(tx_hash_4)
    assert len(scraper.process_available_blocks()) == 3
    assert scraper.emitted_version_data == {
        3: {
            log.address: {
                "packageName": "owned",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            }
        },
        4: {
            log_2.address: {
                "packageName": "other",
                "version": "2",
                "manifestURI": "github.com",
            }
        },
        5: {
            log_2.address: {
                "packageName": "pkg",
                "version": "1.0.0",
                "manifestURI": "www.google.com",
            }
        },
    }


def test_scraper_resolves_nested_uris_and_dependencies(log_pkg):
    log = log_pkg.deployments.get_instance("Log")
    w3 = log_pkg.w3
    tx_hash = log.functions.release(
        "owned", "1.0.0", "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)
    tx_hash_2 = log.functions.release(
        "wallet", "1.0.0", "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash_2)
    scraper = Scraper(w3, w3)
    # This step should be automatic / better integrated into final workflow
    scraper.process_available_blocks()
    assert scraper.emitted_version_data == {
        2: {
            log.address: {
                "packageName": "owned",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW",
            }
        },
        3: {
            log.address: {
                "packageName": "wallet",
                "version": "1.0.0",
                "manifestURI": "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1",
            }
        },
    }
    scraper.resolve_all_manifest_uris()
    assert len(scraper.ipfs_uris) == 7


def test_scraper_resolves_nested_uris_with_github_uris(log_pkg):
    log = log_pkg.deployments.get_instance("Log")
    w3 = log_pkg.w3
    tx_hash = log.functions.release(
        "owned", "1.0.0", "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)
    tx_hash_2 = log.functions.release(
        "wallet",
        "1.0.0",
        "https://api.github.com/repos/ethpm/ethpm-spec/git/blobs/02e437d45b5dd19e1564da416afed439a5324cca",  # noqa: E501
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash_2)
    scraper = Scraper(w3, w3)
    # This step should be automatic / better integrated into final workflow
    scraper.process_available_blocks()
    scraper.resolve_all_manifest_uris()
    assert len(scraper.ipfs_uris) == 6


def test_scraper_writes_to_disk(tmpdir, log_pkg, monkeypatch):
    monkeypatch.chdir(tmpdir)
    w3 = log_pkg.w3
    log = log_pkg.deployments.get_instance("Log")
    tx_hash = log.functions.release(
        "owned", "1.0.0", "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)
    tx_hash_2 = log.functions.release(
        "wallet", "1.0.0", "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash_2)
    scraper = Scraper(w3, w3)
    scraper.process_available_blocks()
    scraper.resolve_all_manifest_uris()
    assert check_dir_trees_equal(scraper.content_dir, TEST_ASSETS)


def test_scraper_imports_existing_content_dir(tmpdir, monkeypatch, log_pkg):
    monkeypatch.chdir(tmpdir)
    ipfs_assets_dir = Path(tmpdir) / "ipfs_assets"
    w3 = log_pkg.w3
    log = log_pkg.deployments.get_instance("Log")
    tx_hash = log.functions.release(
        "owned", "1.0.0", "ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)
    scraper = Scraper(w3, w3)
    scraper.process_available_blocks()
    scraper.resolve_all_manifest_uris()
    tx_hash_2 = log.functions.release(
        "wallet", "1.0.0", "ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1"
    ).transact()
    w3.eth.waitForTransactionReceipt(tx_hash_2)
    scraper_2 = Scraper(w3, w3, ipfs_assets_dir)
    scraper_2.process_available_blocks()
    scraper_2.resolve_all_manifest_uris()
    assert check_dir_trees_equal(scraper_2.content_dir, TEST_ASSETS)

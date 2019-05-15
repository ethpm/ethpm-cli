import itertools
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple  # noqa: F401

from eth_utils import to_dict, to_list
from eth_utils.toolz import assoc
from ethpm.typing import URI, Address
from ethpm.utils.backend import resolve_uri_contents
from ethpm.utils.ipfs import extract_ipfs_path_from_uri, is_ipfs_uri
from ethpm.utils.uri import is_supported_content_addressed_uri
from web3 import Web3

from ethpm_cli._utils.various import flatten
from ethpm_cli.constants import VERSION_RELEASE_ABI
from ethpm_cli.exceptions import BlockAlreadyScrapedError, BlockNotFoundError
from ethpm_cli.validation import validate_chain_data_store

logger = logging.getLogger("ethpm_cli.scraper.Scraper")


BLOCK_INTERVAL = 50

def scrape(w3: Web3, ethpm_dir: Path, start_block: int = 0) -> int:
    """
    Scrapes VersionRelease event data starting from start_block.

    If start_block is 0 (default), scraping begins from the
    max block found in ethpm_dir/chain_data.json.
    """
    initialize_ethpm_dir(ethpm_dir, w3)
    chain_data_path = ethpm_dir / "chain_data.json"
    latest_block = w3.eth.blockNumber

    if start_block >= latest_block:
        raise BlockNotFoundError(
            f"Block number: {start_block} not available on provided web3 "
            f"instance with latest block number of {latest_block}."
        )

    ethpmdir_block = max(get_scraped_blocks(chain_data_path))
    active_block = start_block if start_block else ethpmdir_block

    for from_block in range(active_block, latest_block, BLOCK_INTERVAL):
        if (from_block + BLOCK_INTERVAL) > latest_block:
            to_block = latest_block
        else:
            to_block = from_block + BLOCK_INTERVAL

        if block_range_needs_scraping(from_block, to_block, chain_data_path):
            scraped_manifests = scrape_block_range_for_manifests(w3, from_block, to_block)
            update_chain_data(chain_data_path, from_block, to_block, scraped_manifests)
            write_ipfs_uris_to_disk(ethpm_dir, scraped_manifests)

    return latest_block


def block_range_needs_scraping(from_block: int, to_block: int, chain_data_path: Path) -> bool:
    all_scraped_blocks = get_scraped_blocks(chain_data_path)
    for block in range(from_block, to_block):
        if block not in all_scraped_blocks:
            return True
    return False


def initialize_ethpm_dir(ethpm_dir: Path, w3: Web3) -> None:
    if ethpm_dir.is_dir():
        chain_data_path = ethpm_dir / "chain_data.json"
        validate_chain_data_store(chain_data_path, w3)
    else:
        ethpm_dir.mkdir()
        chain_data_path = ethpm_dir / "chain_data.json"
        chain_data_path.touch()
        init_json = {
            "chain_id": w3.eth.chainId,
            "scraped_blocks": [{"min": "0", "max": "0"}],
        }
        chain_data_path.write_text(f"{json.dumps(init_json, indent=4)}\n")


def update_chain_data(
    chain_data_path: Path, from_block: int, to_block: int, manifests: Dict[Address, Dict[str, str]]
) -> None:
    chain_data = json.loads(chain_data_path.read_text())

    old_scraped_blocks = get_scraped_blocks(chain_data_path)
    new_scraped_blocks = list(range(from_block, to_block))
    updated_blocks = blocks_to_ranges(set(old_scraped_blocks + new_scraped_blocks))

    chain_data_updated_blocks = assoc(chain_data, "scraped_blocks", updated_blocks)
    chain_data_path.write_text(f"{json.dumps(chain_data_updated_blocks, indent=4)}\n")


@to_list
def blocks_to_ranges(blocks_list: List[int]) -> Iterable[Dict[str, str]]:
    """
    Takes a list of block numbers, and returns them grouped into min/max ranges.
    :blocks_list: [0, 1, 2, 4, 6, 9]
    -> [{"min": "0", "max": "2"}, {"min": "4", "max": "4"}, {"min": "6", "max": "9"}]
    """
    for a, b in itertools.groupby(enumerate(blocks_list), lambda x: x[0] - x[1]):
        b = list(b)  # type: ignore
        yield {"min": str(b[0][1]), "max": str(b[-1][1])}  # type: ignore


def get_scraped_blocks(chain_data_path: Path) -> List[int]:
    scraped_blocks = json.loads(chain_data_path.read_text())["scraped_blocks"]
    scraped_ranges = [
        list(range(int(rnge["min"]), int(rnge["max"]) + 1)) for rnge in scraped_blocks
    ]
    return flatten(scraped_ranges)


def write_ipfs_uris_to_disk(
    ethpm_dir: Path, manifests: Dict[Address, Dict[str, str]]
) -> None:
    all_manifest_uris = [
        version_release_data["manifestURI"]
        for version_release_data in manifests.values()
        if is_supported_content_addressed_uri(version_release_data["manifestURI"])
    ]
    base_ipfs_uris = [uri for uri in all_manifest_uris if is_ipfs_uri(uri)]
    nested_ipfs_uris = [pluck_ipfs_uris_from_manifest(uri) for uri in all_manifest_uris]
    all_ipfs_uris = set(flatten(nested_ipfs_uris) + base_ipfs_uris)
    # ex.
    # ipfs uri: QmdvZEW3AaUntDfFkcbdnYzeLAAeD4YFeixQsdmHF88T6Q
    # dir store: ethpmcli/Qm/dv/ZE/QmdvZEW3AaUntDfFkcbdnYzeLAAeD4YFeixQsdmHF88T6Q
    for uri in all_ipfs_uris:
        ipfs_hash = extract_ipfs_path_from_uri(uri)
        first_two_bytes_dir = ethpm_dir / ipfs_hash[0:2]
        second_two_bytes_dir = first_two_bytes_dir / ipfs_hash[2:4]
        third_two_bytes_dir = second_two_bytes_dir / ipfs_hash[4:6]
        asset_dest_path = third_two_bytes_dir / ipfs_hash

        if not asset_dest_path.is_file():
            if not first_two_bytes_dir.is_dir():
                first_two_bytes_dir.mkdir()
            if not second_two_bytes_dir.is_dir():
                second_two_bytes_dir.mkdir()
            if not third_two_bytes_dir.is_dir():
                third_two_bytes_dir.mkdir()

            asset_dest_path.touch()
            asset_dest_path.write_bytes(resolve_uri_contents(uri))
            logger.info("%s written to\n %s.\n", uri, asset_dest_path)


def scrape_block_range_for_manifests(
    w3: Web3, from_block: int, to_block: int
) -> Dict[Address, Dict[str, str]]:
    version_release_logs = get_block_version_release_logs(w3, from_block, to_block)
    logger.info(
        "Blocks %d-%d scraped. %d VersionRelease events found.",
        from_block, to_block,
        len(version_release_logs),
    )
    if version_release_logs:
        return format_version_release_logs(version_release_logs)
    else:
        return {}


@to_list
def pluck_ipfs_uris_from_manifest(uri: URI) -> Iterable[List[Any]]:
    manifest_contents = json.loads(resolve_uri_contents(uri))
    yield pluck_ipfs_uris(manifest_contents)

    if "build_dependencies" in manifest_contents:
        for dependency_uri in manifest_contents["build_dependencies"].values():
            yield pluck_ipfs_uris_from_manifest(dependency_uri)


@to_list
def pluck_ipfs_uris(manifest: Dict[str, Any]) -> Iterable[List[str]]:
    if "sources" in manifest:
        for source in manifest["sources"].values():
            if is_ipfs_uri(source):
                yield source

    if "meta" in manifest:
        if "links" in manifest["meta"]:
            for link in manifest["meta"]["links"].values():
                if is_ipfs_uri(link):
                    yield link

    if "build_dependencies" in manifest:
        for source in manifest["build_dependencies"].values():
            if is_ipfs_uri(source):
                yield source


@to_dict
def format_version_release_logs(
    all_entries: Dict[Any, Any]
) -> Iterable[Tuple[str, Any]]:
    all_addresses = set(entry["address"] for entry in all_entries)
    for address in all_addresses:
        all_releases_by_address = process_entries(address, all_entries)
        yield address, all_releases_by_address


@to_dict
def process_entries(
    address: Address, all_entries: Dict[Any, Any]
) -> Iterable[Tuple[str, str]]:
    for entry in all_entries:
        if entry["address"] == address:
            logger.info(
                f"<Package {entry['args']['packageName']}=={entry['args']['version']}> released on registry @ {address}.\n"
                f"Manifest URI: {entry['args']['manifestURI']}"
            )
            yield "manifestURI", entry["args"]["manifestURI"]
            yield "packageName", entry["args"]["packageName"]
            yield "version", entry["args"]["version"]


def get_block_version_release_logs(w3: Web3, from_block: int, to_block: int) -> Dict[str, Any]:
    log_contract = w3.eth.contract(abi=VERSION_RELEASE_ABI)
    log_filter = log_contract.events.VersionRelease.createFilter(
        fromBlock=from_block, toBlock=to_block
    )
    return log_filter.get_all_entries()

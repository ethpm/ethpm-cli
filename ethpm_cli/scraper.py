from datetime import datetime
import itertools
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple  # noqa: F401

from eth_typing import URI, Address
from eth_utils import to_dict, to_list
from eth_utils.toolz import assoc
from ethpm._utils.ipfs import extract_ipfs_path_from_uri, is_ipfs_uri
from ethpm.uri import is_supported_content_addressed_uri, resolve_uri_contents
from web3 import Web3

from ethpm_cli._utils.various import flatten
from ethpm_cli.config import write_updated_chain_data
from ethpm_cli.constants import VERSION_RELEASE_ABI
from ethpm_cli.exceptions import BlockNotFoundError

logger = logging.getLogger("ethpm_cli.scraper.Scraper")

# https://github.com/ethereum/EIPs/commit/123b7267b6270914a822001c119d11607e695517
VERSION_RELEASE_TIMESTAMP = 1_552_564_800  # March 14, 2019

BATCH_SIZE = 5000


def scrape(w3: Web3, ethpm_dir: Path, start_block: int = 0) -> int:
    """
    Scrapes VersionRelease event data starting from start_block.

    If start_block is not 0, scraping begins from start_block.
    Otherwise the scraping begins from the ethpm birth block.
    """
    chain_data_path = ethpm_dir / "chain_data.json"
    latest_block = w3.eth.blockNumber

    if start_block >= latest_block:
        raise BlockNotFoundError(
            f"Block number: {start_block} not available on provided web3 "
            f"instance with latest block number of {latest_block}."
        )

    if start_block == 0:
        active_block = get_ethpm_birth_block(
            w3, 0, latest_block, VERSION_RELEASE_TIMESTAMP
        )
    else:
        active_block = start_block

    logger.info("Scraping from block %d.", active_block)
    for from_block in range(active_block, latest_block, BATCH_SIZE):
        if (from_block + BATCH_SIZE) > latest_block:
            to_block = latest_block
        else:
            to_block = from_block + BATCH_SIZE

        if block_range_needs_scraping(from_block, to_block, chain_data_path):
            scraped_manifests = scrape_block_range_for_manifests(
                w3, from_block, to_block
            )
            update_chain_data(chain_data_path, from_block, to_block, scraped_manifests)
            write_ipfs_uris_to_disk(ethpm_dir, scraped_manifests)
        else:
            logger.info("Block range: %d - %d already scraped.", from_block, to_block)

    return latest_block


def get_ethpm_birth_block(
    w3: Web3, from_block: int, to_block: int, target_timestamp: int
) -> int:
    """
    Returns the closest block found before the target_timestamp
    """
    version_release_date = datetime.fromtimestamp(target_timestamp)
    from_date = datetime.fromtimestamp(w3.eth.getBlock(from_block)["timestamp"])
    delta = version_release_date - from_date

    if delta.days <= 0 and from_date < version_release_date:
        while (
            w3.eth.getBlock(from_block)["timestamp"] < version_release_date.timestamp()
        ):
            from_block += 1
        return from_block - 1

    elif from_date < version_release_date:
        updated_block = int((from_block + to_block) / 2)
        return get_ethpm_birth_block(w3, updated_block, to_block, target_timestamp)

    else:
        updated_block = from_block - int(to_block - from_block)
        return get_ethpm_birth_block(w3, updated_block, from_block, target_timestamp)


def block_range_needs_scraping(
    from_block: int, to_block: int, chain_data_path: Path
) -> bool:
    all_scraped_blocks = get_scraped_blocks(chain_data_path)
    if any(block not in all_scraped_blocks for block in range(from_block, to_block)):
        return True
    return False


def update_chain_data(
    chain_data_path: Path,
    from_block: int,
    to_block: int,
    manifests: Dict[Address, Dict[str, str]],
) -> None:
    chain_data = json.loads(chain_data_path.read_text())

    old_scraped_blocks = get_scraped_blocks(chain_data_path)
    new_scraped_blocks = list(range(from_block, to_block))
    updated_blocks = blocks_to_ranges(set(old_scraped_blocks + new_scraped_blocks))

    chain_data_with_updated_blocks = assoc(chain_data, "scraped_blocks", updated_blocks)
    write_updated_chain_data(chain_data_path, chain_data_with_updated_blocks)


@to_list
def blocks_to_ranges(blocks_list: List[int]) -> Iterable[Dict[str, str]]:
    """
    Takes a list of block numbers, and returns them grouped into min/max ranges.
    :blocks_list: [0, 1, 2, 4, 6, 9]
    -> [{"min": "0", "max": "2"}, {"min": "4", "max": "4"}, {"min": "6", "max": "9"}]
    """
    for a, b in itertools.groupby(enumerate(blocks_list), lambda x: x[0] - x[1]):
        c = list(b)
        yield {"min": str(c[0][1]), "max": str(c[-1][1])}


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
        from_block,
        to_block,
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
) -> Iterable[Tuple[Address, Any]]:
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
                "<Package %s==%s> released on registry @ %s.\n" "Manifest URI: %s\n",
                entry["args"]["packageName"],
                entry["args"]["version"],
                address,
                entry["args"]["manifestURI"],
            )
            yield "manifestURI", entry["args"]["manifestURI"]
            yield "packageName", entry["args"]["packageName"]
            yield "version", entry["args"]["version"]


def get_block_version_release_logs(
    w3: Web3, from_block: int, to_block: int
) -> Dict[str, Any]:
    log_contract = w3.eth.contract(abi=VERSION_RELEASE_ABI)
    log_filter = log_contract.events.VersionRelease.createFilter(
        fromBlock=from_block, toBlock=to_block
    )
    return log_filter.get_all_entries()

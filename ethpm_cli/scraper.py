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


def scrape(w3: Web3, ethpm_dir: Path, start_block: int = 0) -> None:
    """
    Scrapes VersionRelease event data starting from start_block.
    """
    chain_data_path = ethpm_dir / "chain_data.json"
    try:
        active_block = import_ethpm_dir(ethpm_dir, w3, start_block)
        scraped_manifests = scrape_block_for_manifests(w3, active_block)

        update_chain_data(chain_data_path, active_block, scraped_manifests)
        write_ipfs_uris_to_disk(ethpm_dir, scraped_manifests)

    except BlockNotFoundError:
        logger.info("No more blocks available.")
        return None

    except BlockAlreadyScrapedError:
        active_block = start_block + 1

    scrape(w3, ethpm_dir, active_block)


def import_ethpm_dir(ethpm_dir: Path, w3: Web3, start_block: int) -> int:
    """
    Returns the latest processed block number found in ethpm_dir.
    If no ethpm_dir found, creates an ethpm_dir and returns a 0.
    """
    if ethpm_dir.is_dir():
        chain_data_path = ethpm_dir / "chain_data.json"
        validate_chain_data_store(chain_data_path, w3)

        if start_block >= w3.eth.blockNumber:
            raise BlockNotFoundError(
                f"Block number: {start_block} not available on provided web3 "
                f"instance with latest block number of {w3.eth.blockNumber}."
            )

        all_scraped_blocks = get_scraped_blocks(chain_data_path)
        if start_block in all_scraped_blocks:
            raise BlockAlreadyScrapedError(
                f"Skipping block #{start_block}. Already processed."
            )
        return start_block
    else:
        ethpm_dir.mkdir()
        # make base dir for all ipfs assets
        (ethpm_dir / "Qm").mkdir()
        chain_data_path = ethpm_dir / "chain_data.json"
        chain_data_path.touch()
        init_json = {
            "chain_id": w3.eth.chainId,
            "registry_addresses": [],
            "scraped_blocks": [{"min": "0", "max": "0"}],
        }
        chain_data_path.write_text(f"{json.dumps(init_json, indent=4)}\n")
        return 1


def update_chain_data(
    chain_data_path: Path, block_number: int, manifests: Dict[Address, Dict[str, str]]
) -> None:
    chain_data = json.loads(chain_data_path.read_text())

    new_addrs = list(manifests.keys())
    updated_addrs = list(sorted(set(chain_data["registry_addresses"] + new_addrs)))

    all_scraped_blocks = get_scraped_blocks(chain_data_path)
    updated_blocks = blocks_to_ranges(set(all_scraped_blocks + [block_number]))

    chain_data_updated_blocks = assoc(chain_data, "scraped_blocks", updated_blocks)
    chain_data_updated_addrs = assoc(
        chain_data_updated_blocks, "registry_addresses", updated_addrs
    )
    chain_data_path.write_text(f"{json.dumps(chain_data_updated_addrs, indent=4)}\n")


@to_list
def blocks_to_ranges(blocks_list: List[int]) -> Iterable[Dict[str, str]]:
    """
    Takes a list of block numbers, and returns them grouped into min/max ranges.
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
    ipfs_dir = ethpm_dir / "Qm"
    all_manifest_uris = [
        version_release_data["manifestURI"]
        for version_release_data in manifests.values()
        if is_supported_content_addressed_uri(version_release_data["manifestURI"])
    ]
    base_ipfs_uris = [uri for uri in all_manifest_uris if is_ipfs_uri(uri)]
    nested_ipfs_uris = [pluck_ipfs_uris_from_manifest(uri) for uri in all_manifest_uris]
    all_ipfs_uris = set(flatten(nested_ipfs_uris) + base_ipfs_uris)
    for uri in all_ipfs_uris:
        ipfs_hash = extract_ipfs_path_from_uri(uri)
        unique_hash_prefix_dir = ipfs_dir / ipfs_hash[2:4]
        remainder_hash_dir = unique_hash_prefix_dir / ipfs_hash[4:]

        if not unique_hash_prefix_dir.is_dir():
            unique_hash_prefix_dir.mkdir()

        if not remainder_hash_dir.is_dir():
            remainder_hash_dir.mkdir()
            asset_dest_path = remainder_hash_dir / ipfs_hash
            asset_dest_path.touch()
            asset_dest_path.write_bytes(resolve_uri_contents(uri))
            logger.info("%s written to disk.", uri)


def scrape_block_for_manifests(
    w3: Web3, block_number: int
) -> Dict[Address, Dict[str, str]]:
    version_release_logs = get_block_version_release_logs(w3, block_number)
    logger.info(
        "Block # %d scraped. %d VersionRelease events found in block.",
        block_number,
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
            yield "manifestURI", entry["args"]["manifestURI"]
            yield "packageName", entry["args"]["packageName"]
            yield "version", entry["args"]["version"]


def get_block_version_release_logs(w3: Web3, block_number: int) -> Dict[str, Any]:
    log_contract = w3.eth.contract(abi=VERSION_RELEASE_ABI)
    log_filter = log_contract.events.VersionRelease.createFilter(
        fromBlock=block_number, toBlock=block_number
    )
    return log_filter.get_all_entries()

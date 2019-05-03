from collections import OrderedDict
import itertools
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple  # noqa: F401

from eth_utils import to_dict, to_int, to_list
from eth_utils.toolz import assoc, assoc_in
from ethpm.typing import URI, Address
from ethpm.utils.backend import resolve_uri_contents
from ethpm.utils.ipfs import extract_ipfs_path_from_uri, is_ipfs_uri
from ethpm.utils.uri import is_supported_content_addressed_uri
from web3 import Web3

from ethpm_cli._utils.various import flatten
from ethpm_cli.constants import VERSION_RELEASE_ABI
from ethpm_cli.exceptions import BlockNotFoundError, InstallError, BlockAlreadyScrapedError

logger = logging.getLogger("ethpm_cli.scraper.Scraper")


def scrape(w3: Web3, ethpm_dir: Path, start_block: int=0) -> None:
    """
    if no start_block provided:
        start from the most recently processed block
    """
    # change start_block name and import_ethpm_dir
    chain_data_path = ethpm_dir / 'chain_data.json'
    try:
        active_block = import_ethpm_dir(ethpm_dir, w3, start_block)
        validate_block(chain_data_path, active_block, w3)
        manifests = scrape_manifests_from_chain(w3, active_block)
        update_chain_data(chain_data_path, active_block)
        write_ipfs_uris_to_disk(chain_data_path, manifests)
    except BlockNotFoundError:
        logger.info("No more blocks available.")
        return None
    except BlockAlreadyScrapedError:
        active_block = start_block + 1
    
    scrape(w3, ethpm_dir, active_block)


def import_ethpm_dir(ethpm_dir: Path, w3: Web3, start_block) -> int:
    """
    Returns the last processed block number found in ethpm_dir.
    If no ethpm_dir found, creates an ethpm_dir and returns a 0.

    if no start_block given - starts from maximum scraped
    if start_block given - starts from start_block 
    """
    if ethpm_dir.is_dir():
        chain_data_path = ethpm_dir / 'chain_data.json'
        if not chain_data_path.is_file():
            raise InstallError(
                f"{ethpm_dir} does not appear to be a valid EthPM CLI datastore."
            )

        chain_data = json.loads(chain_data_path.read_text())
        if chain_data["chain_id"] != w3.eth.chainId:
            raise InstallError(
                f"Chain ID found in EthPM CLI datastore: {chain_data['chain_id']} "
                f"does not match chain ID of provided web3 instance: {w3.eth.chainId}"
            )

        if start_block >= w3.eth.blockNumber:
            raise BlockNotFoundError

        all_scraped_blocks = get_scraped_blocks(chain_data_path)
        if start_block in all_scraped_blocks:
            raise BlockAlreadyScrapedError("xxx")

        return start_block

    else:
        ethpm_dir.mkdir()
        chain_data_path = ethpm_dir / 'chain_data.json'
        chain_data_path.touch()
        init_json = {
            "chain_id": w3.eth.chainId,
            "scraped_blocks": [{
                "min": "0",
                "max": "0",
            }]
        }
        chain_data_path.write_text(json.dumps(init_json, indent=4))
        return 1


def update_chain_data(
    chain_data_path: Path, block_number: int
) -> None:
    chain_data = json.loads(chain_data_path.read_text())
    scraped_blocks = get_scraped_blocks(chain_data_path)
    if block_number in scraped_blocks:
        raise BlockNotFoundError("skipping: block already scraped")

    updated_blocks = set(scraped_blocks + [block_number])
    updated_blocks_final = blocks_to_ranges(updated_blocks)
    updated_chain_data = assoc(chain_data, 'scraped_blocks', updated_blocks_final)
    chain_data_path.write_text(json.dumps(updated_chain_data, indent=4))

    
@to_list
def blocks_to_ranges(blocks_list):
    for a, b in itertools.groupby(enumerate(blocks_list), lambda x: x[0] - x[1]):
        b = list(b)
        yield {'min': str(b[0][1]), 'max': str(b[-1][1])}


def get_scraped_blocks(chain_data_path):
    scraped_blocks = json.loads(chain_data_path.read_text())['scraped_blocks']
    scraped_ranges = [list(range(int(rnge['min']), int(rnge['max']) + 1)) for rnge in scraped_blocks]
    return flatten(scraped_ranges)


def validate_block(chain_data_path, block_number, w3):
    if block_number > w3.eth.blockNumber:
        raise BlockNotFoundError(
            f"Block number: {block_number} not available on provided web3 instance "
            f"with latest block number of {w3.eth.blockNumber}."
        )
    scraped_blocks = get_scraped_blocks(chain_data_path)
    if block_number in scraped_blocks:
        raise BlockNotFoundError("skipping: block {block_number} already scraped")


def write_ipfs_uris_to_disk(ethpm_dir: Path, manifests) -> None:
    all_version_release_data = itertools.chain.from_iterable(
        [log.values() for log in manifests.values()]
    )
    all_manifest_uris = [
        data["manifestURI"]
        for data in all_version_release_data
        if is_supported_content_addressed_uri(data["manifestURI"])
    ]
    all_base_ipfs_uris = [uri for uri in all_manifest_uris if is_ipfs_uri(uri)]
    all_nested_ipfs_uris = [
        pluck_ipfs_uris_from_manifest(uri) for uri in all_manifest_uris
    ]
    ipfs_uris = set(flatten(all_nested_ipfs_uris) + all_base_ipfs_uris)
    for uri in ipfs_uris:
        f = ethpm_dir / extract_ipfs_path_from_uri(uri)
        if not f.is_file():
            f.touch()
            f.write_bytes(resolve_uri_contents(uri))
            logger.info('%s written to disk.', uri)


def scrape_manifests_from_chain(w3: Web3, block_number: int) -> Tuple[int, Any]:
    version_release_logs = get_block_version_release_logs(w3, block_number)
    logger.info(
        "Block # %d scraped. %d VersionRelease events found in block.",
        block_number,
        len(version_release_logs),
    )

    if version_release_logs:
        formatted_logs = format_version_release_logs(version_release_logs)
        return formatted_logs
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

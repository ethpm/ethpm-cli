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
from ethpm_cli.exceptions import BlockNotFoundError, InstallError

logger = logging.getLogger("ethpm_cli.scraper.Scraper")


def scrape(w3: Web3, ethpmcli_dir: Path) -> None:
    latest_block_number = import_ethpmcli_dir(ethpmcli_dir, w3)
    try:
        last_block, manifests = scrape_manifests_from_chain(w3, latest_block_number + 1)
        update_ethpmcli_dir(ethpmcli_dir, last_block, manifests)
    except BlockNotFoundError:
        write_ipfs_uris_to_disk(ethpmcli_dir)
    else:
        scrape(w3, ethpmcli_dir)


def import_ethpmcli_dir(ethpmcli_dir: Path, w3: Web3) -> int:
    """
    Returns the last processed block number found in ethpmcli_dir.
    If no ethpmcli_dir found, creates an ethpmcli_dir and returns a 0.
    """
    event_data_path = ethpmcli_dir / "event_data.json"
    if ethpmcli_dir.is_dir():
        if not event_data_path.is_file():
            raise InstallError(
                f"{ethpmcli_dir} does not appear to be a valid EthPM CLI datastore."
            )

        ethpmcli_data = json.loads(event_data_path.read_text())
        if ethpmcli_data["chain_id"] != w3.eth.chainId:
            raise InstallError(
                f"Chain ID found in EthPM CLI datastore: {ethpmcli_data['chain_id']} "
                f"does not match chain ID of provided web3 instance: {w3.eth.chainId}"
            )
        return to_int(text=ethpmcli_data["last_processed_block"])
    else:
        ethpmcli_dir.mkdir()
        event_data_path.touch()
        init_json = {
            "chain_id": w3.eth.chainId,
            "last_processed_block": "0",
            "event_data": {},
        }
        event_data_path.write_text(json.dumps(init_json, indent=4))
        return 0


def update_ethpmcli_dir(
    ethpmcli_dir: Path, block_number: int, manifests: Dict[str, Any]
) -> None:
    event_data_path = ethpmcli_dir / "event_data.json"
    base_event_data = json.loads(
        event_data_path.read_text(), object_pairs_hook=OrderedDict
    )
    updated_block = assoc(base_event_data, "last_processed_block", str(block_number))
    if manifests:
        updated_event_data = assoc_in(
            updated_block, ["event_data", str(block_number)], manifests
        )
        event_data_path.write_text(f"{json.dumps(updated_event_data, indent=4)}\n")
    else:
        event_data_path.write_text(f"{json.dumps(updated_block, indent=4)}\n")


def write_ipfs_uris_to_disk(ethpmcli_dir: Path) -> None:
    version_release_data = json.loads((ethpmcli_dir / "event_data.json").read_text())[
        "event_data"
    ]
    all_version_release_data = itertools.chain.from_iterable(
        [log.values() for log in version_release_data.values()]
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
        f = ethpmcli_dir / extract_ipfs_path_from_uri(uri)
        if not f.is_file():
            f.touch()
            f.write_bytes(resolve_uri_contents(uri))


def scrape_manifests_from_chain(w3: Web3, block_number: int) -> Tuple[int, Any]:
    version_release_logs = get_block_version_release_logs(w3, block_number)
    logger.info(
        "Block # %d scraped. %d VersionRelease events found in block.",
        block_number,
        len(version_release_logs),
    )

    if version_release_logs:
        formatted_logs = format_version_release_logs(version_release_logs)
        return block_number, formatted_logs
    else:
        return block_number, {}


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
    if block_number > w3.eth.blockNumber:
        raise BlockNotFoundError(
            f"Block number: {block_number} not available on provided web3 instance "
            f"with latest block number of {w3.eth.blockNumber}."
        )

    log_contract = w3.eth.contract(abi=VERSION_RELEASE_ABI)
    log_filter = log_contract.events.VersionRelease.createFilter(
        fromBlock=block_number, toBlock=block_number
    )
    return log_filter.get_all_entries()

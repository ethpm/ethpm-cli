from collections import OrderedDict
import itertools
import json
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple  # noqa: F401

from eth_utils import to_dict, to_hex, to_int, to_list
from eth_utils.toolz import assoc
from ethpm.typing import URI, Address
from ethpm.utils.backend import resolve_uri_contents
from ethpm.utils.ipfs import extract_ipfs_path_from_uri, is_ipfs_uri
from ethpm.utils.uri import is_supported_content_addressed_uri
from web3 import Web3
from web3._utils.events import get_event_data

from ethpm_cli._utils.various import flatten
from ethpm_cli.constants import (
    CONTENT_DIR,
    EVENT_ABI as VERSION_RELEASE_EVENT_ABI,
    TOPIC,
)
from ethpm_cli.exceptions import BlockNotFoundError, InstallError


class Scraper:
    """
    Scrape blockchain for all valid 'VersionRelease' events
    Resolves manifest uris & nested uris to a json object
    """

    def __init__(
        self,
        w3: Web3,
        ws_w3: Web3 = None,
        content_dir: Path = None,
        logger: Logger = None,
    ) -> None:
        self.w3 = w3
        # websocket w3 instance needed since infura requires ws for certain jsonrpc calls
        self.ws_w3 = ws_w3 or w3
        self.version_release_data: OrderedDict[str, Any] = OrderedDict()
        self.last_processed_block = 0
        self.ipfs_uris: Set[URI] = set()
        self.logger = logger
        if content_dir:
            self.import_content_dir(content_dir)
        else:
            self.content_dir = Path.cwd() / CONTENT_DIR
            if self.content_dir.exists():
                raise InstallError(
                    "IPFS assets directory already exists, please provide "
                    "its path as your content_dir."
                )
            self.content_dir.mkdir()
            (self.content_dir / "event_data.json").touch()

    def import_content_dir(self, content_dir: Path) -> None:
        # todo: validate content dir & event_data.json against a schema
        event_data = json.loads((content_dir / "event_data.json").read_text())
        if event_data["chain_id"] != self.w3.eth.chainId:
            raise InstallError(
                f"Chain ID of provided web3 instance: {self.w3.eth.chainId} "
                "does not match chain ID in IPFS assets datastore: "
                f"{event_data['chain_id']}."
            )
        self.last_processed_block = to_int(text=event_data["last_processed_block"])
        self.version_release_data = event_data["event_data"]
        self.content_dir = content_dir

    def process_available_blocks(self) -> Dict[str, str]:
        """
        Processes blocks continuously, scraping for VersionRelease events,
        until it catches up with newest mined block on the web3 instance.
        Writes all scraped data to event_data.json then writes new ipfs files to disk.
        """
        version_release_logs = get_block_version_release_logs(
            self.ws_w3, self.last_processed_block
        )

        if version_release_logs:
            formatted_logs = format_version_release_logs(version_release_logs)
            self.version_release_data = assoc(
                self.version_release_data,
                str(self.last_processed_block),
                formatted_logs,
            )

        self.logger.info(
            f"Block #:{self.last_processed_block} scraped. "
            f"{len(version_release_logs)} VersionRelease events found in block."
        )

        all_version_data = {
            "chain_id": self.w3.eth.chainId,
            "last_processed_block": str(self.last_processed_block),
            "event_data": self.version_release_data,
        }
        (self.content_dir / "event_data.json").write_text(
            f"{json.dumps(all_version_data, indent=4)}\n"
        )

        if self.last_processed_block < self.w3.eth.blockNumber:
            self.last_processed_block += 1
            self.process_available_blocks()

        self.write_ipfs_uris_to_disk()
        return self.version_release_data

    def write_ipfs_uris_to_disk(self) -> None:
        all_version_release_data = itertools.chain.from_iterable(
            [log.values() for log in self.version_release_data.values()]
        )
        all_manifest_uris = [
            data["manifestURI"]
            for data in all_version_release_data
            if is_supported_content_addressed_uri(data["manifestURI"])
        ]
        all_base_ipfs_uris = [uri for uri in all_manifest_uris if is_ipfs_uri(uri)]
        all_nested_ipfs_uris = [
            self.pluck_ipfs_uris_from_manifest(uri) for uri in all_manifest_uris
        ]
        self.ipfs_uris = set(flatten(all_nested_ipfs_uris) + all_base_ipfs_uris)
        for uri in self.ipfs_uris:
            f = self.content_dir / extract_ipfs_path_from_uri(uri)
            if not f.is_file():
                f.touch()
                f.write_bytes(resolve_uri_contents(uri))

    @to_list
    def pluck_ipfs_uris_from_manifest(self, uri: URI) -> Iterable[List[Any]]:
        manifest_contents = json.loads(resolve_uri_contents(uri))
        yield pluck_ipfs_uris(manifest_contents)

        if "build_dependencies" in manifest_contents:
            for dependency_uri in manifest_contents["build_dependencies"].values():
                yield self.pluck_ipfs_uris_from_manifest(dependency_uri)


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

    log_filter = w3.eth.filter(
        {
            "fromBlock": to_hex(block_number),
            "toBlock": to_hex(block_number),
            "topics": [TOPIC],
        }
    )
    log_filter.log_entry_formatter = get_event_data(VERSION_RELEASE_EVENT_ABI)
    return log_filter.get_all_entries()

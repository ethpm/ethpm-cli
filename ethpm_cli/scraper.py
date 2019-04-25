from ethpm_cli.constants import EVENT_ABI, TOPIC, CONTENT_DIR
from pathlib import Path
from ethpm.utils.ipfs import is_ipfs_uri, extract_ipfs_path_from_uri
import itertools
from eth_utils.toolz import assoc
from eth_utils import to_dict, to_list, to_int
from web3._utils.events import get_event_data
import json
from ethpm.utils.backend import resolve_uri_contents
from ethpm.utils.uri import is_supported_content_addressed_uri
from ethpm_cli._utils.various import flatten

# - what about disconnects / interruptions
# - error handling if ipfs content is unavailable
# - backdoor to pin any ipfs asset
# - update to use new entries
# - have a logger output found versions
# - keep pinging for unfound assets
# - util to regularly pin all assets to infura / any node / local node


class Scraper:
    """
    Scrapes blockchain for all valid 'VersionRelease' events
    Resolves manifest uris & nested uris to a json object
    """
    def __init__(self, w3, ws_w3=None, content_dir=None, block_no=None):
        self.w3 = w3
        self.ws_w3 = ws_w3
        self.emitted_version_data = {}
        self.last_processed_block = block_no if block_no else 0
        self.ipfs_uris = []
        if content_dir:
            self.import_content_dir(content_dir)
        else:
            self.content_dir = Path.cwd() / CONTENT_DIR
            if not self.content_dir.is_dir():
                self.content_dir.mkdir()
            (self.content_dir / "event_data.json").touch()

    def import_content_dir(self, content_dir):
        event_data = json.loads((content_dir / "event_data.json").read_text())
        if event_data["chain_id"] != self.w3.eth.chainId:
            raise Exception

        all_processed_blocks = event_data["event_data"].keys()
        self.last_processed_block = to_int(text=max(all_processed_blocks))
        self.content_dir = content_dir

    def process_available_blocks(self):
        if self.last_processed_block > self.w3.eth.blockNumber:
            raise Exception

        log_filter = self.ws_w3.eth.filter(
            {
                "fromBlock": self.w3.toHex(self.last_processed_block),
                "toBlock": self.w3.toHex(self.last_processed_block),
                "topics": [TOPIC],
            }
        )
        log_filter.log_entry_formatter = get_event_data(EVENT_ABI)
        version_release_logs = log_filter.get_all_entries()
        formatted_logs = format_version_release_logs(version_release_logs)
        if formatted_logs:
            self.emitted_version_data = assoc(
                self.emitted_version_data, self.last_processed_block, formatted_logs
            )

        if self.last_processed_block < self.w3.eth.blockNumber:
            self.last_processed_block += 1
            self.process_available_blocks()

        all_version_data = {
            "chain_id": self.w3.eth.chainId,
            "event_data": self.emitted_version_data,
        }
        (self.content_dir / "event_data.json").write_text(
            f"{json.dumps(all_version_data, indent=4, sort_keys=True)}\n"
        )
        return self.emitted_version_data

    def resolve_all_manifest_uris(self):
        all_logged_data = itertools.chain.from_iterable(
            [x.values() for x in self.emitted_version_data.values()]
        )
        all_logged_uris = [
            data["manifestURI"]
            for data in all_logged_data
            if is_supported_content_addressed_uri(data["manifestURI"])
        ]
        all_nested_ipfs_uris = [
            self.resolve(manifest_uri) for manifest_uri in all_logged_uris
        ]
        all_base_ipfs_uris = [uri for uri in all_logged_uris if is_ipfs_uri(uri)]
        self.ipfs_uris = set(flatten(all_nested_ipfs_uris) + all_base_ipfs_uris)
        for uri in self.ipfs_uris:
            f = self.content_dir / extract_ipfs_path_from_uri(uri)
            if not f.is_file():
                f.touch()
                f.write_bytes(resolve_uri_contents(uri))

    @to_list
    def resolve(self, uri):
        # error handling? contents not available
        manifest_contents = json.loads(resolve_uri_contents(uri))

        yield pluck_manifest_ipfs_uris(manifest_contents)

        if "build_dependencies" in manifest_contents:
            for dependency_uri in manifest_contents["build_dependencies"].values():
                yield self.resolve(dependency_uri)


@to_list
def pluck_manifest_ipfs_uris(manifest):
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
def format_version_release_logs(entries):
    for entry in entries:
        yield entry["address"], process_args(entry["args"])


@to_dict
def process_args(args):
    yield "packageName", args["packageName"]
    yield "version", args["version"]
    yield "manifestURI", args["manifestURI"]

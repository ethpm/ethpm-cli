import json
import os
from typing import Any, Dict, Iterable, Tuple
from urllib import parse

from eth_typing import URI
from eth_utils import to_dict, to_hex, to_int
from ethpm.backends.base import BaseURIBackend
from ethpm.tools import builder
from ethpm.uri import create_latest_block_uri
import requests

from ethpm_cli._utils.etherscan import get_etherscan_network, is_etherscan_uri
from ethpm_cli.config import get_ipfs_backend, setup_w3
from ethpm_cli.constants import ETHERSCAN_KEY_ENV_VAR
from ethpm_cli.exceptions import ContractNotVerified
from ethpm_cli.validation import validate_etherscan_key_available


class EtherscanURIBackend(BaseURIBackend):
    def can_resolve_uri(self, uri: URI) -> bool:
        return False

    def can_translate_uri(self, uri: URI) -> bool:
        return is_etherscan_uri(uri)

    def fetch_uri_contents(
        self, uri: URI, package_name: str, package_version: str
    ) -> URI:
        manifest = build_etherscan_manifest(uri, package_name, package_version)
        ipfs_backend = get_ipfs_backend()
        ipfs_data = builder.build(
            manifest, builder.validate(), builder.pin_to_ipfs(backend=ipfs_backend)
        )
        return URI(f"ipfs://{ipfs_data[0]['Hash']}")


@to_dict
def build_etherscan_manifest(
    uri: URI, package_name: str, version: str
) -> Iterable[Tuple[str, Any]]:
    address, chain_id = parse.urlparse(uri).netloc.split(":")
    network = get_etherscan_network(chain_id)
    body = make_etherscan_request(address, network)
    contract_type = body["ContractName"]
    w3 = setup_w3(to_int(text=chain_id))
    block_uri = create_latest_block_uri(w3)
    runtime_bytecode = to_hex(w3.eth.getCode(address))

    yield "package_name", package_name
    yield "version", version
    yield "manifest_version", "2"
    yield "sources", {f"./{contract_type}.sol": body["SourceCode"]}
    yield "contract_types", {
        contract_type: {
            "abi": json.loads(body["ABI"]),
            "runtime_bytecode": {"bytecode": runtime_bytecode},
            "compiler": generate_compiler_info(body),
        }
    }
    yield "deployments", {
        block_uri: {contract_type: {"contract_type": contract_type, "address": address}}
    }


def make_etherscan_request(contract_addr: str, network: str) -> Dict[str, Any]:
    validate_etherscan_key_available()
    etherscan_api_key = os.getenv(ETHERSCAN_KEY_ENV_VAR)
    etherscan_req_uri = f"https://api{network}.etherscan.io/api"
    response = requests.get(  # type: ignore
        etherscan_req_uri,
        params=[
            ("module", "contract"),
            ("action", "getsourcecode"),
            ("address", contract_addr),
            ("apikey", etherscan_api_key),
        ],
    ).json()
    return parse_etherscan_response(response, contract_addr)


def parse_etherscan_response(
    response: Dict[str, Any], contract_addr: str
) -> Dict[str, Any]:
    if response["message"] == "NOTOK":
        raise ContractNotVerified(
            f"Contract at {contract_addr} unavailable or has not been verified on Etherscan."
        )
    return response["result"][0]


@to_dict
def generate_compiler_info(body: Dict[str, Any]) -> Iterable[Tuple[str, Any]]:
    if "vyper" in body["CompilerVersion"]:
        name, version = body["CompilerVersion"].split(":")
    else:
        name = "solc"
        version = body["CompilerVersion"]

    optimized = True if body["OptimizationUsed"] == 1 else False

    yield "name", name
    yield "version", version
    yield "settings", {"optimize": optimized}

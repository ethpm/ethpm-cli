from typing import Any
from urllib import parse

from eth_typing import URI
from eth_utils import is_hex_address

ETHERSCAN_SUPPORTED_CHAIN_IDS = {
    "1": "",
    "3": "-ropsten",
    "4": "-rinkeby",
    "5": "-goerli",
    "42": "-kovan",
}


def is_etherscan_uri(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    parsed = parse.urlparse(value)
    if parsed.scheme != "etherscan" or not parsed.netloc or not parsed.path:
        return False

    contract_address = parsed.netloc
    chain_id = parsed.path.lstrip("/")

    if not is_hex_address(contract_address):
        return False

    if chain_id not in ETHERSCAN_SUPPORTED_CHAIN_IDS:
        return False

    return True


def get_etherscan_network(uri: URI) -> str:
    parsed = parse.urlparse(uri)
    chain_id = parsed.path.lstrip("/")
    return ETHERSCAN_SUPPORTED_CHAIN_IDS[chain_id]

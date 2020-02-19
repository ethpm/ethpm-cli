from typing import Any, Tuple
from urllib import parse

from eth_utils import is_checksum_address

ETHERSCAN_SUPPORTED_CHAIN_IDS = {
    "1": "",  # mainnet
    "3": "-ropsten",
    "4": "-rinkeby",
    "5": "-goerli",
    "42": "-kovan",
}


def is_etherscan_uri(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    parsed = parse.urlparse(value)
    if parsed.scheme != "etherscan" or not parsed.netloc:
        return False

    if parsed.path:
        return False

    address, chain_id = parse_etherscan_uri(value)
    if not is_checksum_address(address):
        return False

    if chain_id not in ETHERSCAN_SUPPORTED_CHAIN_IDS:
        return False

    return True


def parse_etherscan_uri(uri: str) -> Tuple[str, str]:
    parsed = parse.urlparse(uri)
    if ":" in parsed.netloc:
        address, _, chain_id = parsed.netloc.partition(":")
    else:
        address, chain_id = (parsed.netloc, "1")
    return address, chain_id


def get_etherscan_network(chain_id: str) -> str:
    return ETHERSCAN_SUPPORTED_CHAIN_IDS[chain_id]

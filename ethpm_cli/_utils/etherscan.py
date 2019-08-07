from typing import Any
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

    if ":" not in parsed.netloc:
        return False

    address, chain_id = parsed.netloc.split(":")
    if not is_checksum_address(address):
        return False

    if chain_id not in ETHERSCAN_SUPPORTED_CHAIN_IDS:
        return False

    return True


def get_etherscan_network(chain_id: str) -> str:
    return ETHERSCAN_SUPPORTED_CHAIN_IDS[chain_id]

import json

from eth_utils import keccak, to_hex
from ethpm.constants import INFURA_API_KEY

CONTENT_DIR = "ipfs_assets"
ETHPM_DIR_NAME = "ethpm_packages"
EVENT_ABI = json.loads(
    """
        {"anonymous":false,"inputs":[{"indexed":false,"name":"packageName","type":"string"},
        {"indexed":false,"name":"version","type":"string"},
        {"indexed":false,"name":"manifestURI","type":"string"}],"name":"VersionRelease","type":"event"}
    """
)
TOPIC = to_hex(keccak(text="VersionRelease(string,string,string)"))

INFURA_HTTP_URI = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
INFURA_WS_URI = f"wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}"

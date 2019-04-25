import json

from eth_utils import to_hex, keccak

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

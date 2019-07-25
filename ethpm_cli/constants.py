import json

from ethpm_cli import CLI_ASSETS_DIR

ETHPM_DIR_ENV_VAR = "ETHPM_CLI_PACKAGES_DIR"
ETHPM_PACKAGES_DIR = "_ethpm_packages"
IPFS_ASSETS_DIR = "ipfs"
IPFS_CHAIN_DATA = "chain_data.json"
KEYFILE_PATH = "_ethpm_keyfile.json"
LOCKFILE_NAME = "ethpm.lock"
SRC_DIR_NAME = "_src"

VERSION_RELEASE_ABI = json.loads((CLI_ASSETS_DIR / "1.0.1.json").read_text())[
    "contract_types"
]["Log"]["abi"]
INFURA_HTTP_URI = f"https://mainnet.infura.io/v3/4f1a358967c7474aae6f8f4a7698aefc"

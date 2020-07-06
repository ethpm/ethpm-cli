import json

import pkg_resources

from ethpm_cli import CLI_ASSETS_DIR

ETHPM_DIR_ENV_VAR = "ETHPM_CLI_PACKAGES_DIR"
ETHPM_PACKAGES_DIR = "_ethpm_packages"
IPFS_ASSETS_DIR = "ipfs"
IPFS_CHAIN_DATA = "chain_data.json"
KEYFILE_PATH = "_ethpm_keyfile.json"
LOCKFILE_NAME = "ethpm.lock"
REGISTRY_STORE = "_ethpm_registries.json"
SOLC_INPUT = "solc_input.json"
SOLC_OUTPUT = "solc_output.json"
SOLC_PATH = "ETHPM_CLI_SOLC_PATH"
SRC_DIR_NAME = "_src"

VERSION_RELEASE_ABI = json.loads((CLI_ASSETS_DIR / "v3.json").read_text())[
    "contractTypes"
]["Log"]["abi"]
INFURA_HTTP_URI = "https://mainnet.infura.io/v3/4f1a358967c7474aae6f8f4a7698aefc"
ETHPM_CLI_VERSION = pkg_resources.require("ethpm-cli")[0].version
ETHERSCAN_KEY_ENV_VAR = "ETHPM_CLI_ETHERSCAN_API_KEY"

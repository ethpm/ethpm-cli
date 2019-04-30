import json

from ethpm.constants import INFURA_API_KEY

from ethpm_cli import CLI_ASSETS_DIR

ETHPM_DIR_NAME = "ethpm_packages"
VERSION_RELEASE_ABI = json.loads((CLI_ASSETS_DIR / "1.0.1.json").read_text())[
    "contract_types"
]["Log"]["abi"]
INFURA_HTTP_URI = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"

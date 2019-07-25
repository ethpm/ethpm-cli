from argparse import Namespace
import json
import os
from pathlib import Path
from typing import Any, Dict

from ethpm.constants import SUPPORTED_CHAIN_IDS
from web3 import Web3
from web3.auto.infura.endpoints import build_http_headers, build_infura_url
from web3.providers.auto import load_provider_from_uri

from ethpm_cli._utils.filesystem import atomic_replace
from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.constants import (
    ETHPM_DIR_ENV_VAR,
    ETHPM_PACKAGES_DIR,
    IPFS_CHAIN_DATA,
    KEYFILE_PATH,
)
from ethpm_cli.exceptions import ValidationError
from ethpm_cli.validation import validate_ethpm_dir


class Config:
    """
    Class to manage CLI config options
    - Validate / Initialize xdg ethpm dir
    - IPFS Backend
    - Validate / Initialize ethpm packages dir
    - Setup w3
    """

    def __init__(self, args: Namespace) -> None:
        # Setup IPFS backend
        if "local_ipfs" in args and args.local_ipfs:
            self.ipfs_backend = get_ipfs_backend(args.local_ipfs)
        else:
            self.ipfs_backend = get_ipfs_backend()

        # Setup _ethpm_packages dir
        if "ethpm_dir" in args and args.ethpm_dir:
            self.ethpm_dir = args.ethpm_dir
        elif ETHPM_DIR_ENV_VAR in os.environ:
            self.ethpm_dir = Path(os.environ[ETHPM_DIR_ENV_VAR])
        else:
            self.ethpm_dir = Path.cwd() / ETHPM_PACKAGES_DIR
            if not self.ethpm_dir.is_dir():
                self.ethpm_dir.mkdir()
        validate_ethpm_dir(self.ethpm_dir)

        # Setup w3
        if "chain_id" in args and args.chain_id:
            self.w3 = get_w3(args.chain_id)
        else:
            self.w3 = get_w3(1)

        # Setup xdg ethpm dir
        xdg_ethpmcli_root = get_xdg_ethpmcli_root()
        setup_xdg_ethpm_dir(xdg_ethpmcli_root, self.w3)


def get_w3(chain_id: int) -> Web3:
    if chain_id not in SUPPORTED_CHAIN_IDS.keys():
        raise ValidationError(
            f"Chain ID: {chain_id} is invalid. Currently supported chain ids "
            f"include: {list(SUPPORTED_CHAIN_IDS.keys())}."
        )
    infura_url = f"{SUPPORTED_CHAIN_IDS[chain_id]}.infura.io"
    headers = build_http_headers()
    infura_url = build_infura_url(infura_url)
    return Web3(load_provider_from_uri(infura_url, headers))


def setup_xdg_ethpm_dir(xdg_ethpmcli_root: Path, w3: Web3) -> None:
    if not xdg_ethpmcli_root.is_dir():
        initialize_xdg_ethpm_dir(xdg_ethpmcli_root, w3)

    if not (xdg_ethpmcli_root / IPFS_CHAIN_DATA).is_file():
        raise ValidationError(
            f"Invalid xdg ethpm dir found @ {xdg_ethpmcli_root}. No IPFS chain data file found."
        )

    if not (xdg_ethpmcli_root / KEYFILE_PATH).is_file():
        raise ValidationError(
            f"Invalid xdg ethpm dir found @ {xdg_ethpmcli_root}. No keyfile found."
        )


def initialize_xdg_ethpm_dir(xdg_ethpmcli_root: Path, w3: Web3) -> None:
    xdg_ethpmcli_root.mkdir()
    os.environ["XDG_ETHPMCLI_ROOT"] = str(xdg_ethpmcli_root)
    xdg_chain_data = xdg_ethpmcli_root / IPFS_CHAIN_DATA
    xdg_chain_data.touch()
    init_chain_data = {
        "chain_id": w3.eth.chainId,
        "scraped_blocks": [{"min": "0", "max": "0"}],
    }
    write_updated_chain_data(xdg_chain_data, init_chain_data)
    xdg_keyfile = xdg_ethpmcli_root / KEYFILE_PATH
    xdg_keyfile.touch()


def write_updated_chain_data(
    chain_data_path: Path, updated_data: Dict[str, Any]
) -> None:
    with atomic_replace(chain_data_path) as chain_data_file:
        chain_data_file.write(json.dumps(updated_data, indent=4))
        chain_data_file.write("\n")

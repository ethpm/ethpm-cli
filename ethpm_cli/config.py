from argparse import Namespace
import json
from pathlib import Path
import os
import shutil
import tempfile
from typing import Any, Dict

from web3 import Web3
from web3.providers.auto import load_provider_from_uri

from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.constants import ETHPM_DIR_NAME, INFURA_HTTP_URI, IPFS_CHAIN_DATA, KEYFILE_PATH
from ethpm_cli.exceptions import ValidationError
from ethpm_cli.validation import validate_chain_data_store, validate_ethpm_dir


class Config:
    """
    Class to manage CLI config options
    - Init xdg ethpm dir
    - IPFS Backend
    - Target ethpm_dir
    """
    def __init__(self, args: Namespace) -> None:
        if "local_ipfs" in args:
            self.ipfs_backend = get_ipfs_backend(args.local_ipfs)
        else:
            self.ipfs_backend = get_ipfs_backend()

        if args.ethpm_dir:
            self.ethpm_dir = args.ethpm_dir
        elif ETHPM_DIR_ENV_VAR in os.environ:
            self.ethpm_dir = Path(os.environ[ETHPM_DIR_ENV_VAR])
        else:
            self.ethpm_dir = Path.cwd() / ETHPM_DIR_NAME
            if not self.ethpm_dir.is_dir():
                self.ethpm_dir.mkdir()
        validate_ethpm_dir(self.ethpm_dir)

        # Setup xdg ethpm dir
        xdg_ethpm_dir = get_xdg_ethpmcli_root()
        w3 = Web3(load_provider_from_uri(INFURA_HTTP_URI))
        if xdg_ethpm_dir.is_dir():
            validate_xdg_ethpm_dir(xdg_ethpm_dir, w3)
        else:
            initialize_xdg_ethpm_dir(xdg_ethpm_dir, w3)


def validate_xdg_ethpm_dir(xdg_dir, w3):
    chain_data_path = xdg_dir / IPFS_CHAIN_DATA
    validate_chain_data_store(chain_data_path, w3)
    if not (xdg_dir / KEYFILE_PATH).is_file():
        raise ValidationError(
            f"Invalid xdg ethpm dir found @ {xdg_dir}. No keyfile found."
        )


def initialize_xdg_ethpm_dir(ethpm_dir: Path, w3: Web3) -> None:
    ethpm_dir.mkdir()
    os.environ['XDG_ETHPMCLI_ROOT'] = str(ethpm_dir)
    chain_data_path = ethpm_dir / IPFS_CHAIN_DATA
    chain_data_path.touch()
    init_json = {
        "chain_id": w3.eth.chainId,
        "scraped_blocks": [{"min": "0", "max": "0"}],
    }
    write_updated_chain_data(chain_data_path, init_json)
    ethpm_keyfile = ethpm_dir / KEYFILE_PATH
    ethpm_keyfile.touch()


def write_updated_chain_data(
    chain_data_path: Path, updated_data: Dict[str, Any]
) -> None:
    tmp_pkg_dir = Path(tempfile.mkdtemp())
    tmp_data = tmp_pkg_dir / "chain_data.json"
    tmp_data.write_text(f"{json.dumps(updated_data, indent=4)}\n")
    shutil.copyfile(tmp_data, chain_data_path)

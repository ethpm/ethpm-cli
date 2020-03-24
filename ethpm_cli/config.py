from argparse import Namespace
import json
import os
from pathlib import Path
from typing import Any, Dict

from eth_account import Account
from eth_utils import to_checksum_address
from ethpm.constants import SUPPORTED_CHAIN_IDS
from web3 import Web3
from web3.auto.infura.endpoints import build_http_headers, build_infura_url
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.providers.auto import load_provider_from_uri

from ethpm_cli._utils.filesystem import atomic_replace
from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.commands.auth import get_authorized_private_key, import_keyfile
from ethpm_cli.constants import (
    ETHPM_DIR_ENV_VAR,
    ETHPM_PACKAGES_DIR,
    IPFS_CHAIN_DATA,
    KEYFILE_PATH,
)
from ethpm_cli.exceptions import ConfigurationError, ValidationError
from ethpm_cli.validation import validate_ethpm_dir, validate_project_directory


class Config:
    """
    Class to manage CLI config options
    - Validate / Initialize xdg ethpm dir
    - IPFS Backend
    - Validate / Initialize ethpm packages dir
    - Setup w3
    - Projects dir
    """

    private_key = None

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
            chain_id = args.chain_id
        else:
            chain_id = 1

        if "keyfile_path" in args and args.keyfile_path:
            import_keyfile(args.keyfile_path)

        if "keyfile_password" in args and args.keyfile_password:
            self.private_key = get_authorized_private_key(args.keyfile_password)
        self.w3 = setup_w3(chain_id, self.private_key)

        # Setup xdg ethpm dir
        self.xdg_ethpmcli_root = get_xdg_ethpmcli_root()
        setup_xdg_ethpm_dir(self.xdg_ethpmcli_root, self.w3)

        # Setup projects dir
        if "project_dir" in args and args.project_dir:
            validate_project_directory(args.project_dir)
            self.project_dir = args.project_dir
        else:
            self.project_dir = None

        if "manifest_path" in args and args.manifest_path:
            if not args.manifest_path.is_file():
                raise ConfigurationError(
                    f"Provided manifest path: {args.manifest_path} is not a file."
                )
            self.manifest_path = args.manifest_path
        else:
            self.manifest_path = None


def setup_w3(chain_id: int, private_key: str = None) -> Web3:
    if chain_id not in SUPPORTED_CHAIN_IDS.keys():
        raise ValidationError(
            f"Chain ID: {chain_id} is invalid. Currently supported chain ids "
            f"include: {list(SUPPORTED_CHAIN_IDS.keys())}."
        )
    infura_url = f"{SUPPORTED_CHAIN_IDS[chain_id]}.infura.io"
    headers = build_http_headers()
    infura_url = build_infura_url(infura_url)
    w3 = Web3(load_provider_from_uri(infura_url, headers))

    if private_key is not None:
        owner_address = Account.from_key(private_key).address
        signing_middleware = construct_sign_and_send_raw_middleware(private_key)
        w3.middleware_onion.add(signing_middleware)
        # ignore b/c defaultAccount inits as Empty
        w3.eth.defaultAccount = to_checksum_address(owner_address)  # type: ignore
        cli_logger.debug(
            "In-flight tx signing has been enabled for address: {owner_address}."
        )
    w3.enable_unstable_package_management_api()
    return w3


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


def validate_config_has_project_dir_attr(config: Config) -> None:
    if not config.project_dir:
        raise FileNotFoundError(
            "Please provide a project directory containing the contracts you want to package. "
            "For more information on project directory structure, refer to the docs."
        )

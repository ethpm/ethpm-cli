from pathlib import Path
import tempfile
from typing import Any, Dict

import eth_keyfile
from eth_typing import Address
from eth_utils import to_bytes

from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.constants import KEYFILE_PATH
from ethpm_cli.exceptions import AuthorizationError


def import_keyfile(keyfile_path: Path) -> None:
    validate_keyfile(keyfile_path)
    ethpm_xdg_root = get_xdg_ethpmcli_root()
    ethpm_cli_keyfile_path = ethpm_xdg_root / KEYFILE_PATH
    tmp_keyfile = Path(tempfile.NamedTemporaryFile().name)
    tmp_keyfile.write_text(keyfile_path.read_text())
    tmp_keyfile.replace(ethpm_cli_keyfile_path)


def get_keyfile_path() -> Path:
    ethpm_xdg_root = get_xdg_ethpmcli_root()
    keyfile_path = ethpm_xdg_root / KEYFILE_PATH
    if not keyfile_path.is_file():
        raise AuthorizationError(f"No keyfile located at {keyfile_path}.")

    if not keyfile_path.read_text():
        raise AuthorizationError(f"Empty keyfile located at {keyfile_path}.")
    return keyfile_path


def get_keyfile_data() -> Dict[str, Any]:
    keyfile_path = get_keyfile_path()
    return eth_keyfile.load_keyfile(str(keyfile_path))


def validate_keyfile(keyfile_path: Path) -> None:
    keyfile_data = eth_keyfile.load_keyfile(str(keyfile_path))
    if keyfile_data["version"] != 3:
        raise AuthorizationError(
            f"Keyfile found at {keyfile_path} does not look like a supported eth-keyfile object."
        )


def get_authorized_address() -> Address:
    """
    Returns the address associated with stored keyfile. No password required.
    """
    keyfile = get_keyfile_data()
    return keyfile["address"]


def get_authorized_private_key(password: str) -> str:
    """
    Returns the private key associated with stored keyfile. Password required.
    """
    keyfile_path = get_keyfile_path()
    private_key = eth_keyfile.extract_key_from_keyfile(
        str(keyfile_path), to_bytes(text=password)
    )
    return private_key

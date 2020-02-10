import json
from pathlib import Path
from typing import Any, Dict

import eth_keyfile
from eth_typing import Address
from eth_utils import add_0x_prefix, to_bytes

from ethpm_cli._utils.filesystem import atomic_replace
from ethpm_cli._utils.input import parse_bool_flag
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.constants import KEYFILE_PATH
from ethpm_cli.exceptions import AuthorizationError

PRIVATE_KEY_WARNING = (
    "Please be careful when using your private key, it is a sensitive piece of information.\n",
    "~ ~ ~ Not your keys, not your crypto. ~ ~ ~\n",
    "ethPM doesn't save your private key, but it is best practice to re-use an already encrypted ",
    "keyfile and link it with `ethpm auth link` rather than regenerating a new encrypted keyfile.",
)


def link_keyfile(keyfile_path: Path) -> None:
    if valid_keyfile_exists():
        xdg_keyfile = get_keyfile_path()
        cli_logger.info(
            f"Keyfile detected at {xdg_keyfile}. Please use `ethpm auth unlink` to delete this "
            "keyfile before linking a new one."
        )
    else:
        import_keyfile(keyfile_path)
        address = get_authorized_address()
        cli_logger.info(
            f"Keyfile stored for address: {address}\n"
            "It's now available for use when its password is passed in with the "
            "`--keyfile-password` flag."
        )


def unlink_keyfile() -> None:
    if not valid_keyfile_exists():
        cli_logger.info("Unable to unlink keyfile: empty keyfile found.")
    else:
        keyfile_path = get_keyfile_path()
        address = get_authorized_address()
        keyfile_path.write_text("")
        cli_logger.info(f"Keyfile removed for address: {address}")


def init_keyfile() -> None:
    if valid_keyfile_exists():
        cli_logger.info(
            f"Keyfile detected. Please use `ethpm auth unlink` to delete this "
            "keyfile before initializing a new one."
        )
        return

    cli_logger.info(PRIVATE_KEY_WARNING)
    agreement = parse_bool_flag(
        "Are you sure you want to proceed with initializing a keyfile? "
    )
    if not agreement:
        cli_logger.info("Aborting keyfile initialization.")
        return

    private_key = to_bytes(text=input("Please enter your 32-length private key: "))
    validate_private_key_length(private_key)
    password = to_bytes(
        text=input(
            "Please enter a password to encrypt your keyfile with (Don't forget this password!): "
        )
    )
    keyfile_json = eth_keyfile.create_keyfile_json(private_key, password)
    ethpm_xdg_root = get_xdg_ethpmcli_root()
    ethpm_cli_keyfile_path = ethpm_xdg_root / KEYFILE_PATH
    with atomic_replace(ethpm_cli_keyfile_path) as file:
        file.write(json.dumps(keyfile_json))
    address = get_authorized_address()
    cli_logger.info(f"Encrypted keyfile saved for address: {address}")


def valid_keyfile_exists() -> bool:
    try:
        get_authorized_address()
    except AuthorizationError:
        return False
    return True


def validate_private_key_length(private_key: str) -> None:
    if len(private_key) != 32:
        raise AuthorizationError(f"{private_key} is not 32 long")


def import_keyfile(keyfile_path: Path) -> None:
    validate_keyfile(keyfile_path)
    ethpm_xdg_root = get_xdg_ethpmcli_root()
    ethpm_cli_keyfile_path = ethpm_xdg_root / KEYFILE_PATH
    with atomic_replace(ethpm_cli_keyfile_path) as file:
        file.write(keyfile_path.read_text())


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
    return add_0x_prefix(keyfile["address"])


def get_authorized_private_key(password: str) -> str:
    """
    Returns the private key associated with stored keyfile. Password required.
    """
    keyfile_path = get_keyfile_path()
    try:
        private_key = eth_keyfile.extract_key_from_keyfile(
            str(keyfile_path), to_bytes(text=password)
        )
    except ValueError:
        raise AuthorizationError(
            f"Provided keyfile password: {password} is not a valid "
            f"password for encrypted keyfile at {keyfile_path}."
        )
    return private_key

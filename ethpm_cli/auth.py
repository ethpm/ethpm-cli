import os
from typing import Optional

from eth_account import Account
import eth_keyfile
from eth_typing import Address
from eth_utils import to_bytes

from ethpm_cli.constants import KEYFILE_PASSWORD, KEYFILE_PATH
from ethpm_cli.exceptions import ValidationError


def set_auth(keyfile_path: str, password: str) -> None:
    validate_keyfile_path_and_password(keyfile_path, to_bytes(text=password))
    os.environ[KEYFILE_PATH] = keyfile_path
    os.environ[KEYFILE_PASSWORD] = password


def get_authorized_address() -> Address:
    private_key = get_authorized_private_key()
    return Account.from_key(private_key).address


def get_authorized_private_key() -> Optional[str]:
    keyfile_path = os.getenv(KEYFILE_PATH)
    password = to_bytes(text=os.getenv(KEYFILE_PASSWORD))
    if not keyfile_path or not password:
        raise ValidationError(
            "Must set password-protected keyfile via `ethpm auth` command."
        )
    validate_keyfile_path_and_password(keyfile_path, password)
    private_key = eth_keyfile.extract_key_from_keyfile(keyfile_path, password)
    return private_key


def validate_keyfile_path_and_password(keyfile_path: str, password: str) -> None:
    try:
        eth_keyfile.extract_key_from_keyfile(keyfile_path, password)
    except ValueError:
        raise ValidationError(f"Invalid keyfile password.")

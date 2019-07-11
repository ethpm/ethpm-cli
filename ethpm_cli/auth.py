import os
from typing import Optional

from eth_account import Account
from eth_typing import Address

from ethpm_cli.constants import PRIVATE_KEY_ENV_VAR
from ethpm_cli.exceptions import ValidationError


def get_authorized_address() -> Address:
    private_key = get_authorized_private_key()
    return Account.from_key(private_key).address


def get_authorized_private_key() -> Optional[str]:
    private_key = os.getenv(PRIVATE_KEY_ENV_VAR)
    if private_key:
        validate_private_key(private_key)
        return private_key
    return None


def validate_private_key(key: str) -> None:
    if len(key) != 64:
        raise ValidationError(
            f"Private key ({key}) stored under environment variable: "
            f"{PRIVATE_KEY_ENV_VAR} is not a valid private key."
        )

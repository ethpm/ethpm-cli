import json

import eth_keyfile
from eth_utils import to_text
import pytest

from ethpm_cli.auth import (
    get_authorized_address,
    get_authorized_private_key,
    validate_keyfile_path_and_password,
)
from ethpm_cli.constants import KEYFILE_PASSWORD, KEYFILE_PATH
from ethpm_cli.exceptions import ValidationError

PRIVATE_KEY = b"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01"  # noqa: E501
ADDRESS = "0x1a642f0E3c3aF545E7AcBD38b07251B3990914F1"
PASSWORD = b"password"
KEYFILE_JSON = eth_keyfile.create_keyfile_json(PRIVATE_KEY, PASSWORD)


@pytest.fixture
def keyfile(monkeypatch, tmp_path):
    tmp_keyfile = tmp_path / "keyfile.json"
    tmp_keyfile.touch()
    tmp_keyfile.write_text(json.dumps(KEYFILE_JSON))
    monkeypatch.setenv(KEYFILE_PASSWORD, to_text(PASSWORD))
    monkeypatch.setenv(KEYFILE_PATH, str(tmp_keyfile))
    return tmp_keyfile


def test_get_auth_private_key(keyfile):
    actual_priv_key = get_authorized_private_key()
    assert actual_priv_key == PRIVATE_KEY


def test_get_authorized_address(keyfile):
    auth_address = get_authorized_address()
    assert auth_address == ADDRESS


def test_validate_keyfile_path_and_password(keyfile):
    with pytest.raises(ValidationError, match="Invalid keyfile password."):
        validate_keyfile_path_and_password(str(keyfile), b"invalid")

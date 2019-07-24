from pathlib import Path
import tempfile
import filecmp
import json
import os

import eth_keyfile
from eth_utils import is_same_address, to_text
import pytest

from ethpm_cli.auth import (
    get_authorized_address,
    get_authorized_private_key,
    import_keyfile,
)
from ethpm_cli.constants import KEYFILE_PASSWORD, KEYFILE_PATH
from ethpm_cli.exceptions import ValidationError

PRIVATE_KEY = b"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01"  # noqa: E501
ADDRESS = "0x1a642f0E3c3aF545E7AcBD38b07251B3990914F1"
PASSWORD = b"password"
KEYFILE_JSON = eth_keyfile.create_keyfile_json(PRIVATE_KEY, PASSWORD)


@pytest.fixture
def keyfile(monkeypatch, tmpdir):
    monkeypatch.chdir(tmpdir)
    ethpmcli_dir = Path(tmpdir / "ethpmcli_dir")
    ethpmcli_dir.mkdir()
    monkeypatch.setenv("XDG_ETHPMCLI_ROOT", str(ethpmcli_dir))
    tmp_keyfile = ethpmcli_dir / KEYFILE_PATH
    tmp_keyfile.touch()
    tmp_keyfile.write_text(json.dumps(KEYFILE_JSON))
    return tmp_keyfile


def test_import_keyfile(keyfile):
    # is this even testing anything useful?
    ethpmcli_dir = Path(os.environ["XDG_ETHPMCLI_ROOT"])
    import_keyfile(keyfile)
    assert filecmp.cmp(ethpmcli_dir / KEYFILE_PATH, keyfile)


def test_get_authorized_address(keyfile):
    auth_address = get_authorized_address()
    assert is_same_address(auth_address, ADDRESS)


def test_get_authorized_private_key(keyfile):
    actual_priv_key = get_authorized_private_key(to_text(PASSWORD))
    assert actual_priv_key == PRIVATE_KEY

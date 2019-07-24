import filecmp
import json
import os
from pathlib import Path

import eth_keyfile
from eth_utils import is_same_address, to_text
import pytest

from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.auth import (
    get_authorized_address,
    get_authorized_private_key,
    get_keyfile_path,
    import_keyfile,
)
from ethpm_cli.constants import KEYFILE_PATH


@pytest.fixture
def keyfile_auth():
    private_key = b"\x01" * 32
    address = "0x1a642f0E3c3aF545E7AcBD38b07251B3990914F1"
    password = b"password"
    return private_key, address, password


# move to conftest
@pytest.fixture
def keyfile(keyfile_auth):
    private_key, _, password = keyfile_auth
    xdg_ethpm_dir = get_xdg_ethpmcli_root()
    assert 'pytest' in str(xdg_ethpm_dir)
    tmp_keyfile = xdg_ethpm_dir / KEYFILE_PATH
    keyfile_json = eth_keyfile.create_keyfile_json(private_key, password)
    tmp_keyfile.write_text(json.dumps(keyfile_json))
    return tmp_keyfile


def test_import_keyfile(keyfile):
    ethpmcli_dir = get_xdg_ethpmcli_root()
    import_keyfile(keyfile)
    assert filecmp.cmp(ethpmcli_dir / KEYFILE_PATH, keyfile)


def test_get_authorized_address(keyfile, keyfile_auth):
    _, expected_address, _ = keyfile_auth
    actual_address = get_authorized_address()
    assert is_same_address(actual_address, expected_address)


def test_get_authorized_private_key(keyfile, keyfile_auth):
    expected_private_key, _, password = keyfile_auth
    actual_priv_key = get_authorized_private_key(to_text(password))
    assert actual_priv_key == expected_private_key


def test_keyfile_fixture_exposes_tmp_dirs_not_user_dirs(keyfile):
    path = get_keyfile_path()
    assert "pytest" in str(path)

import filecmp

from eth_utils import is_same_address, to_text

from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.auth import (
    get_authorized_address,
    get_authorized_private_key,
    get_keyfile_path,
    import_keyfile,
)
from ethpm_cli.constants import KEYFILE_PATH


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

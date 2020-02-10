import json

import pexpect
import pytest
from web3.auto.infura import w3

from ethpm_cli.config import initialize_xdg_ethpm_dir
from ethpm_cli.constants import KEYFILE_PATH
from ethpm_cli.main import ENTRY_DESCRIPTION

# taken from eth-keyfile readme
PRIVATE_KEY = b"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01"  # noqa: E501
PASSWORD = b"foo"
ENCRYPTED_KEYFILE_JSON = '{"address": "1a642f0e3c3af545e7acbd38b07251b3990914f1", "crypto": {"cipher": "aes-128-ctr", "cipherparams": {"iv": "6087dab2f9fdbbfaddc31a909735c1e6"}, "ciphertext": "5318b4d5bcd28de64ee5559e671353e16f075ecae9f99c7a79a38af5f869aa46", "kdf": "pbkdf2", "kdfparams": {"c": 262144, "dklen": 32, "prf": "hmac-sha256", "salt": "ae3cd4e7013836a3df6bd7241b12db061dbe2c6785853cce422d148a624ce0bd"}, "mac": "517ead924a9d0dc3124507e3393d175ce3ff7c1e96529c6c555ce9e51205e9b2"}, "id": "3198bc9c-6672-5ab3-d995-4942343ae5b6", "version": 3}'  # noqa: E501


@pytest.fixture
def tmp_xdg(tmp_path, monkeypatch):
    tmp_xdg_dir = tmp_path / "xdg"
    initialize_xdg_ethpm_dir(tmp_xdg_dir, w3)

    tmp_keyfile = tmp_path / "keyfile.json"
    tmp_keyfile.write_text(ENCRYPTED_KEYFILE_JSON)
    return tmp_xdg_dir, tmp_keyfile


def test_auth_without_keyfile(tmp_xdg):
    child = pexpect.spawn("ethpm auth")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(f"No valid keyfile found.")


def test_auth_link_keyfile(tmp_xdg):
    tmp_xdg_dir, tmp_keyfile = tmp_xdg
    child = pexpect.spawn(f"ethpm auth link --keyfile-path {tmp_keyfile}")
    child.expect("\r\n")
    child.expect(
        f"Keyfile stored for address: 0x1a642f0e3c3af545e7acbd38b07251b3990914f1"
    )
    child.expect(
        "It's now available for use when its password is passed in with the "
        "`--keyfile-password` flag."
    )
    assert (tmp_xdg_dir / KEYFILE_PATH).read_text() == tmp_keyfile.read_text()


def test_auth_link_requires_keyfile_path_flag(tmp_xdg):
    child = pexpect.spawn(f"ethpm auth link")
    child.expect("\r\n")
    child.expect(f"Invalid --keyfile-path flag")


def test_auth_link_with_invalid_keyfile(tmp_xdg):
    tmp_xdg_dir, _ = tmp_xdg
    invalid_keyfile = tmp_xdg_dir / "invalid.json"
    invalid_keyfile.write_text(json.dumps({"version": 4}))
    child = pexpect.spawn(f"ethpm auth link --keyfile-path {invalid_keyfile}")
    child.expect("\r\n")
    child.expect(
        f"Keyfile found at {invalid_keyfile} does not look like a supported eth-keyfile object."
    )


def test_auth_link_with_existing_keyfile(tmp_xdg):
    tmp_xdg_dir, tmp_keyfile = tmp_xdg
    (tmp_xdg_dir / KEYFILE_PATH).write_text(ENCRYPTED_KEYFILE_JSON)
    child = pexpect.spawn(f"ethpm auth link --keyfile-path {tmp_keyfile}")
    child.expect("\r\n")
    child.expect(
        f"Keyfile detected at {tmp_xdg_dir / KEYFILE_PATH}. Please use "
        "`ethpm auth unlink` to delete this"
    )


def test_auth_unlink(tmp_xdg):
    tmp_xdg_dir, tmp_keyfile = tmp_xdg
    (tmp_xdg_dir / KEYFILE_PATH).write_text(ENCRYPTED_KEYFILE_JSON)
    child = pexpect.spawn(f"ethpm auth unlink")
    child.expect("\r\n")
    child.expect(
        "Keyfile removed for address: 0x1a642f0e3c3af545e7acbd38b07251b3990914f1"
    )


def test_auth_unlink_without_stored_keyfile(tmp_xdg):
    tmp_xdg_dir, tmp_keyfile = tmp_xdg
    (tmp_xdg_dir / KEYFILE_PATH).write_text("")
    child = pexpect.spawn(f"ethpm auth unlink")
    child.expect("\r\n")
    child.expect("Unable to unlink keyfile: empty keyfile found.")


def test_auth_init(tmp_xdg):
    tmp_xdg_dir, tmp_keyfile = tmp_xdg
    (tmp_xdg_dir / KEYFILE_PATH).write_text("")
    child = pexpect.spawn(f"ethpm auth init")
    child.expect("\r\n")
    child.expect(
        "Please be careful when using your private key, it is a sensitive piece of information."
    )
    child.expect("Are you sure you want to proceed with initializing a keyfile?")
    child.sendline("Y")
    child.expect("Please enter your 32-length private key:")
    child.sendline(PRIVATE_KEY)
    child.expect("Please enter a password to encrypt your keyfile with")
    child.sendline(PASSWORD)
    child.expect("Encrypted keyfile saved for address:")
    actual_keyfile_json = json.loads((tmp_xdg_dir / KEYFILE_PATH).read_text())
    expected_keyfile_json = json.loads(ENCRYPTED_KEYFILE_JSON)
    assert actual_keyfile_json["address"] == expected_keyfile_json["address"]
    assert actual_keyfile_json["version"] == expected_keyfile_json["version"]


def test_auth_init_abort(tmp_xdg):
    tmp_xdg_dir, tmp_keyfile = tmp_xdg
    (tmp_xdg_dir / KEYFILE_PATH).write_text("")
    child = pexpect.spawn(f"ethpm auth init")
    child.expect("\r\n")
    child.expect("Are you sure you want to proceed with initializing a keyfile?")
    child.sendline("n")
    child.expect("Aborting keyfile initialization")


def test_auth_init_with_existing_keyfile(tmp_xdg):
    tmp_xdg_dir, tmp_keyfile = tmp_xdg
    (tmp_xdg_dir / KEYFILE_PATH).write_text(ENCRYPTED_KEYFILE_JSON)
    child = pexpect.spawn(f"ethpm auth init")
    child.expect("\r\n")
    child.expect("Keyfile detected.")

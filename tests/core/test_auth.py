import pytest

from ethpm_cli.auth import get_authorized_address, get_authorized_private_key
from ethpm_cli.constants import PRIVATE_KEY_ENV_VAR

PRIVATE_KEY = "b1febf5283d3514c7bc5be3ce6b034d227c8159e85bb6e958181cd09525ce5b9"
ADDRESS = "0xabc4FC248969137A5078DE7b685C4E7f7AC3Be26"


def test_get_auth_private_key(monkeypatch):
    monkeypatch.setenv(PRIVATE_KEY_ENV_VAR, PRIVATE_KEY)
    actual_priv_key = get_authorized_private_key()
    assert actual_priv_key == PRIVATE_KEY


@pytest.mark.parametrize(
    "key",
    (
        1,
        {},
        None,
        True,
        "xxx",
        # 63 chars
        "000000000000000000000000000000000000000000000000000000000000000",
        # 65 chars
        "00000000000000000000000000000000000000000000000000000000000000000",
    ),
)
def test_get_auth_private_key_raises_exception_with_invalid_key(key, monkeypatch):
    monkeypatch.setenv(PRIVATE_KEY_ENV_VAR, key)
    with pytest.raises(Exception, match="is not a valid private key."):
        get_authorized_private_key()


def test_get_authorized_address(monkeypatch):
    monkeypatch.setenv(PRIVATE_KEY_ENV_VAR, PRIVATE_KEY)
    auth_address = get_authorized_address()
    assert auth_address == ADDRESS

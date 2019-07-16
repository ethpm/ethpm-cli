import pexpect
from pathlib import Path
from ethpm_cli.constants import ETHPM_DIR_NAME

def test_ethpm_registry_list(tmpdir):
    tmp_ethpm_dir = Path(tmpdir) / ETHPM_DIR_NAME
    tmp_ethpm_dir.mkdir()
    add_child = pexpect.spawn("ethpm registry add erc1319://0x1230000000000000000000000000000000000000:1 --alias mine")
    add_child.expect("EthPM CLI v0.1.0a0\r\n")
    add_child.expect("\r\n")
    add_child.expect("Registry @ erc1319://0x1230000000000000000000000000000000000000:1 added to registry store.")
    child = pexpect.spawn(f"ethpm registry list --ethpm-dir {tmp_ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect("erc1319://0x1230000000000000000000000000000000000000:1 --- mine (active)")

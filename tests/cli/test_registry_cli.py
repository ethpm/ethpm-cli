from pathlib import Path

import pexpect

from ethpm_cli.constants import ETHPM_DIR_NAME


def test_ethpm_registry_commands(tmpdir):
    tmp_ethpm_dir = Path(tmpdir) / ETHPM_DIR_NAME
    tmp_ethpm_dir.mkdir()
    # test registry add
    add_child = pexpect.spawn(
        f"ethpm registry add erc1319://0x1230000000000000000000000000000000000000:1 --alias mine --ethpm-dir {tmp_ethpm_dir}"  # noqa: E501
    )
    add_child.expect("EthPM CLI v0.1.0a0\r\n")
    add_child.expect("\r\n")
    add_child.expect(
        r"Registry @ erc1319://0x1230000000000000000000000000000000000000:1 \(alias: mine\) added to registry store."  # noqa: E501
    )
    # test registry list
    child = pexpect.spawn(f"ethpm registry list --ethpm-dir {tmp_ethpm_dir}")
    child.expect("EthPM CLI v0.1.0a0\r\n")
    child.expect("\r\n")
    child.expect(
        r"erc1319://0x1230000000000000000000000000000000000000:1 --- mine \(active\)"
    )
    # add second registry
    child_add = pexpect.spawn(
        f"ethpm registry add erc1319://0xabc0000000000000000000000000000000000000:3 --alias yours --ethpm-dir {tmp_ethpm_dir}"  # noqa: E501
    )
    child_add.expect("EthPM CLI v0.1.0a0\r\n")
    child_add.expect("\r\n")
    child_add.expect(
        r"Registry @ erc1319://0xabc0000000000000000000000000000000000000:3 \(alias: yours\) added to registry store."  # noqa: E501
    )
    # activate using alias
    child_act = pexpect.spawn(
        f"ethpm registry activate yours --ethpm-dir {tmp_ethpm_dir}"
    )
    child_act.expect("EthPM CLI v0.1.0a0\r\n")
    child_act.expect("\r\n")
    child_act.expect("Registry @ yours activated.")
    # check activation successful
    child_two = pexpect.spawn(f"ethpm registry list --ethpm-dir {tmp_ethpm_dir}")
    child_two.expect("EthPM CLI v0.1.0a0\r\n")
    child_two.expect("\r\n")
    child_two.expect(r"erc1319://0x1230000000000000000000000000000000000000:1 --- mine")
    child_two.expect(
        r"erc1319://0xabc0000000000000000000000000000000000000:3 --- yours \(active\)"
    )
    # activate using registry uri
    child_three = pexpect.spawn(
        f"ethpm registry activate erc1319://0x1230000000000000000000000000000000000000:1 --ethpm-dir {tmp_ethpm_dir}"  # noqa: E501
    )
    child_three.expect("EthPM CLI v0.1.0a0\r\n")
    child_three.expect("\r\n")
    child_three.expect(
        "Registry @ erc1319://0x1230000000000000000000000000000000000000:1 activated."
    )
    # check activation successful
    child_four = pexpect.spawn(f"ethpm registry list --ethpm-dir {tmp_ethpm_dir}")
    child_four.expect("EthPM CLI v0.1.0a0\r\n")
    child_four.expect("\r\n")
    child_four.expect(
        r"erc1319://0x1230000000000000000000000000000000000000:1 --- mine \(active\)"
    )
    child_four.expect(
        r"erc1319://0xabc0000000000000000000000000000000000000:3 --- yours"
    )

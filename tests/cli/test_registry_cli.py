import pexpect

from ethpm_cli.constants import ETHPM_CLI_VERSION


def test_ethpm_registry_commands():
    # test registry add
    add_child = pexpect.spawn(
        f"ethpm registry add erc1319://0x1230000000000000000000000000000000000000:1 --alias mine"
    )
    add_child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    add_child.expect("\r\n")
    add_child.expect(
        r"Registry @ erc1319://0x1230000000000000000000000000000000000000:1 \(alias: mine\) added to registry store."  # noqa: E501
    )

    # test registry list
    child = pexpect.spawn(f"ethpm registry list")
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(
        r"erc1319://0x1230000000000000000000000000000000000000:1 --- mine \(active\)"
    )

    # add second registry
    child_add = pexpect.spawn(
        f"ethpm registry add erc1319://0xabc0000000000000000000000000000000000000:3 --alias yours"  # noqa: E501
    )
    child_add.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child_add.expect("\r\n")
    child_add.expect(
        r"Registry @ erc1319://0xabc0000000000000000000000000000000000000:3 \(alias: yours\) added to registry store."  # noqa: E501
    )

    # activate using alias
    child_act = pexpect.spawn(f"ethpm registry activate yours")
    child_act.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child_act.expect("\r\n")
    child_act.expect("Registry @ yours activated.")

    # check activation successful
    child_two = pexpect.spawn(f"ethpm registry list")
    child_two.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child_two.expect("\r\n")
    child_two.expect(r"erc1319://0x1230000000000000000000000000000000000000:1 --- mine")
    child_two.expect(
        r"erc1319://0xabc0000000000000000000000000000000000000:3 --- yours \(active\)"
    )

    # activate using registry uri
    child_three = pexpect.spawn(
        f"ethpm registry activate erc1319://0x1230000000000000000000000000000000000000:1"
    )
    child_three.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child_three.expect("\r\n")
    child_three.expect(
        "Registry @ erc1319://0x1230000000000000000000000000000000000000:1 activated."
    )

    # check activation successful
    child_four = pexpect.spawn(f"ethpm registry list")
    child_four.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child_four.expect("\r\n")
    child_four.expect(
        r"erc1319://0x1230000000000000000000000000000000000000:1 --- mine \(active\)"
    )
    child_four.expect(
        r"erc1319://0xabc0000000000000000000000000000000000000:3 --- yours"
    )

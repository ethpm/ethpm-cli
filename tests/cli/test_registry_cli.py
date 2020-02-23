import pexpect

from ethpm_cli.main import ENTRY_DESCRIPTION


def test_ethpm_registry_commands():
    # test registry add
    add_child = pexpect.spawn(
        f"ethpm registry add erc1319://0x1230000000000000000000000000000000000000:1 --alias mine"
    )
    add_child.expect(ENTRY_DESCRIPTION)
    add_child.expect("\r\n")
    add_child.expect(
        r"Registry @ erc1319://0x1230000000000000000000000000000000000000:1 \(alias: mine\) added to registry store."  # noqa: E501
    )

    # test registry list
    child = pexpect.spawn(f"ethpm registry list")
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("erc1319://0x1230000000000000000000000000000000000000:1")
    child.expect("mine")
    child.expect(r"\(active\)")

    # add second registry
    child_add = pexpect.spawn(
        f"ethpm registry add erc1319://0xabc0000000000000000000000000000000000000:3 --alias yours"  # noqa: E501
    )
    child_add.expect(ENTRY_DESCRIPTION)
    child_add.expect("\r\n")
    child_add.expect(
        r"Registry @ erc1319://0xabc0000000000000000000000000000000000000:3 \(alias: yours\) added to registry store."  # noqa: E501
    )

    # activate using alias
    child_act = pexpect.spawn(f"ethpm registry activate yours")
    child_act.expect(ENTRY_DESCRIPTION)
    child_act.expect("\r\n")
    child_act.expect("Registry @ yours activated.")

    # check activation successful
    child_two = pexpect.spawn(f"ethpm registry list")
    child_two.expect(ENTRY_DESCRIPTION)
    child_two.expect("\r\n")
    child_two.expect("erc1319://0x1230000000000000000000000000000000000000:1")
    child_two.expect("mine")
    child_two.expect("erc1319://0xabc0000000000000000000000000000000000000:3")
    child_two.expect("yours")
    child_two.expect(r"\(active\)")

    # activate using registry uri
    child_three = pexpect.spawn(
        f"ethpm registry activate erc1319://0x1230000000000000000000000000000000000000:1"
    )
    child_three.expect(ENTRY_DESCRIPTION)
    child_three.expect("\r\n")
    child_three.expect(
        "Registry @ erc1319://0x1230000000000000000000000000000000000000:1 activated."
    )

    # check activation successful
    child_four = pexpect.spawn(f"ethpm registry list")
    child_four.expect(ENTRY_DESCRIPTION)
    child_four.expect("\r\n")
    child_four.expect("erc1319://0x1230000000000000000000000000000000000000:1")
    child_four.expect("mine")
    child_four.expect(r"\(active\)")
    child_four.expect("erc1319://0xabc0000000000000000000000000000000000000:3")
    child_four.expect("yours")

    # test registry explore
    child_five = pexpect.spawn(
        f"ethpm registry explore erc1319://0x16763EaE3709e47eE6140507Ff84A61c23B0098A:1"
    )
    child_five.expect(ENTRY_DESCRIPTION)
    child_five.expect("\r\n")

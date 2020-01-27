import pexpect


def test_parse_bool_flag(tmp_project_dir):
    child = pexpect.spawn(
        f"ethpm create wizard --project-dir {tmp_project_dir}", timeout=5
    )
    child.expect("Enter your package's name: ")
    child.sendline("wallet")
    child.expect("Enter your package's version: ")
    child.sendline("0.0.1")
    child.expect("Would you like to add a description to your package?")

    # test parse bool accepts "n" for False
    child.sendline("n")
    child.expect("Would you like to add a license to your package.")

    # test parse bool accepts "N" for False
    child.sendline("N")
    child.expect("Would you like to add authors to your package?")

    # test parse bool will ask question again if invalid response
    child.sendline("")
    child.expect("Invalid response: .\r\n")
    child.expect("Would you like to add authors to your package?")

    child.sendline("1")
    child.expect("Invalid response: 1.\r\n")
    child.expect("Would you like to add authors to your package?")

    child.sendline("x")
    child.expect("Invalid response: x.\r\n")
    child.expect("Would you like to add authors to your package?")

    # test parse bool accepts "y" for True
    child.sendline("y")
    child.expect("Enter an author, or multiple authors separated by commas: ")
    child.sendline("author")
    child.expect("Would you like to add keywords to your package?")

    # test parse bool accepts "Y" for True
    child.sendline("Y")
    child.expect("Enter a keyword, or multiple keywords separated by commas: ")

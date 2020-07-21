import json

import pexpect

from ethpm_cli.main import ENTRY_DESCRIPTION


def test_get_simple_fetch():
    child = pexpect.spawn(
        "ethpm get ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR"
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("manifest")
    child.expect("authors")
    child.expect("license")
    child.expect("owned")
    child.expect("./Owned.sol")
    child.expect("ipfs://QmU8QUSt56ZoBDJgjjXvAZEPro9LmK1m2gjVG5Q4s9x29W")
    child.expect("1.0.0")


def test_get_pretty_print():
    child = pexpect.spawn(
        "ethpm get ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR --pretty"
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect("Package Name: owned\r\n")
    child.expect("Package Version: 1.0.0\r\n")
    child.expect("Manifest Version: ethpm/3\r\n")
    child.expect("\r\n")
    child.expect("Metadata: \r\n")
    child.expect("Authors: Piper Merriam <pipermerriam@gmail.com>\r\n")
    child.expect("License: MIT\r\n")
    child.expect(
        "Description: Reusable contracts which implement a privileged 'owner' "
        "model for authorization.\r\n"
    )
    child.expect("Keywords: authorization\r\n")
    child.expect(
        "documentation: ipfs://QmUYcVzTfSwJoigggMxeo2g5STWAgJdisQsqcXHws7b1FW\r\n"
    )
    child.expect("Sources: \r\n")
    child.expect("Owned.sol: ipfs://QmU8QUSt56ZoBDJgjjXvAZEPro9LmK1m2gjVG5Q4s9x29W\r\n")
    child.expect("\r\n")
    child.expect("Contract Types: \r\n")
    child.expect("None.\r\n")
    child.expect("\r\n")
    child.expect("Deployments: \r\n")
    child.expect("None.\r\n")
    child.expect("\r\n")
    child.expect("Build Dependencies: \r\n")
    child.expect("None.\r\n")
    child.expect("\r\n")


def test_get_write_to_output_file(tmp_project_dir):
    output_file = tmp_project_dir / "output_file.json"
    child = pexpect.spawn(
        f"ethpm get ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR "
        f"--output-file {output_file}"
    )
    child.expect(ENTRY_DESCRIPTION)
    child.expect("\r\n")
    child.expect(
        f"Manifest sourced from: ipfs://QmcxvhkJJVpbxEAa6cgW3B6XwPJb79w9GpNUv2P2THUzZR "
        f"written to {output_file}"
    )
    assert output_file.is_file()
    actual_manifest = json.loads(output_file.read_text())
    assert actual_manifest["name"] == "owned"


def test_get_output_file_and_pretty_print_are_mutually_exclusive(tmp_project_dir):
    output_file = tmp_project_dir / "output_file.json"
    child = pexpect.spawn(
        f"ethpm get ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW "
        f"--output-file {output_file} --pretty"
    )
    child.expect("argument --pretty: not allowed with argument --output-file")

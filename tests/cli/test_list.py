import pexpect

from ethpm_cli.constants import ETHPM_CLI_VERSION


def test_ethpm_list(test_assets_dir):
    ethpm_dir = test_assets_dir / "multiple" / "_ethpm_packages"
    child = pexpect.spawn(f"ethpm list --ethpm-dir {ethpm_dir}")
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(
        r"owned==1.0.0 --- \(ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW\)\r\n"
    )
    child.expect(
        r"wallet==1.0.0 --- \(ipfs://QmRMSm4k37mr2T3A2MGxAj2eAHGR5veibVt1t9Leh5waV1\)\r\n"
    )
    child.expect(
        r"- safe-math-lib==1.0.0 --- \(ipfs://QmWgvM8yXGyHoGWqLFXvareJsoCZVsdrpKNCLMun3RaSJm\)\r\n"
    )
    child.expect(
        r"- owned==1.0.0 --- \(ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW\)\r\n"
    )


def test_ethpm_list_with_aliased_package(test_assets_dir):
    ethpm_dir = test_assets_dir / "owned" / "ipfs_uri_alias" / "_ethpm_packages"
    child = pexpect.spawn(f"ethpm list --ethpm-dir {ethpm_dir}")
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(
        "owned @ owned-alias==1.0.0 --- "
        r"\(ipfs://QmbeVyFLSuEUxiXKwSsEjef6icpdTdA4kGG9BcrJXKNKUW\)\r\n"
    )


def test_unsupported_command():
    child = pexpect.spawn("ethpm invalid")
    child.expect(f"ethPM CLI v{ETHPM_CLI_VERSION}\r\n")
    child.expect("\r\n")
    child.expect(
        "ethpm: error: argument command: invalid choice: 'invalid' "
        r"\(choose from 'auth', 'registry', 'create', 'scrape', "
        r"'install', 'uninstall', 'list'\)\r\n"
    )

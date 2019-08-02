import argparse
from pathlib import Path

from eth_utils import humanize_hash

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.solc import generate_solc_input
from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.auth import get_authorized_address, import_keyfile
from ethpm_cli.config import Config
from ethpm_cli.constants import IPFS_CHAIN_DATA
from ethpm_cli.exceptions import AuthorizationError, InstallError, ValidationError
from ethpm_cli.install import (
    install_package,
    list_installed_packages,
    uninstall_package,
)
from ethpm_cli.manifest import generate_basic_manifest, generate_custom_manifest
from ethpm_cli.package import Package
from ethpm_cli.registry import activate_registry, add_registry, list_registries
from ethpm_cli.scraper import scrape
from ethpm_cli.validation import (
    validate_chain_data_store,
    validate_install_cli_args,
    validate_solc_output,
    validate_uninstall_cli_args,
)

parser = argparse.ArgumentParser(description="ethpm-cli")
ethpm_parser = parser.add_subparsers(help="commands", dest="command")


def add_chain_id_arg_to_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--chain-id",
        dest="chain_id",
        action="store",
        type=int,
        help="Chain ID of target blockchain.",
    )


def add_ethpm_dir_arg_to_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--ethpm-dir",
        dest="ethpm_dir",
        action="store",
        type=Path,
        help="Path to specific ethPM directory (Defaults to ``./_ethpm_packages``).",
    )


#
# ethpm auth
#


def auth_action(args: argparse.Namespace) -> None:
    Config(args)
    if args.keyfile_path:
        import_keyfile(args.keyfile_path)
    try:
        authorized_address = get_authorized_address()
        cli_logger.info(f"Keyfile stored for address: 0x{authorized_address}.")
    except AuthorizationError:
        cli_logger.info(
            "No valid keyfile found. Use `ethpm auth --keyfile-path <path_to_keyfile>` "
            "to set your keyfile for use with ethPM CLI."
        )


auth_parser = ethpm_parser.add_parser("auth", help="auth")
auth_parser.add_argument(
    "--keyfile-path",
    dest="keyfile_path",
    action="store",
    type=Path,
    help="Path to your keyfile.",
)
auth_parser.set_defaults(func=auth_action)


#
# ethpm registry
#


def registry_list_cmd(args: argparse.Namespace) -> None:
    config = Config(args)
    list_registries(config)


def registry_add_cmd(args: argparse.Namespace) -> None:
    config = Config(args)
    add_registry(args.uri, args.alias, config)
    if args.alias:
        log_msg = (
            f"Registry @ {args.uri} (alias: {args.alias}) added to registry store."
        )
    else:
        log_msg = f"Registry @ {args.uri} added to registry store."
    cli_logger.info(log_msg)


def registry_activate_cmd(args: argparse.Namespace) -> None:
    config = Config(args)
    activate_registry(args.uri_or_alias, config)
    cli_logger.info(f"Registry @ {args.uri_or_alias} activated.")


registry_parser = ethpm_parser.add_parser("registry")
registry_subparsers = registry_parser.add_subparsers(help="registry", dest="registry")

registry_list_parser = registry_subparsers.add_parser("list", help="list")
add_ethpm_dir_arg_to_parser(registry_list_parser)
registry_list_parser.set_defaults(func=registry_list_cmd)

registry_add_parser = registry_subparsers.add_parser("add", help="add")
registry_add_parser.add_argument(
    "uri", action="store", type=str, help="Registry URI for target registry."
)
registry_add_parser.add_argument(
    "--alias",
    dest="alias",
    action="store",
    type=str,
    help="Alias with which to reference this registry.",
)
add_ethpm_dir_arg_to_parser(registry_add_parser)
registry_add_parser.set_defaults(func=registry_add_cmd)

registry_activate_parser = registry_subparsers.add_parser("activate", help="activate")
registry_activate_parser.add_argument(
    "uri_or_alias",
    action="store",
    type=str,
    help="Registry URI or alias for target registry.",
)
add_ethpm_dir_arg_to_parser(registry_activate_parser)
registry_activate_parser.set_defaults(func=registry_activate_cmd)


#
# ethpm create
#


def create_action(args: argparse.Namespace) -> None:
    config = Config(args)
    if not config.project_dir:
        raise FileNotFoundError(
            "Please provide a project directory containing the contracts you want to package. "
            "For more information on project directory structure, refer to the docs."
        )

    # ethpm create --solc-input
    if args.solc_input:
        generate_solc_input(args.project_dir / "contracts")

    # ethpm create --manifest-wizard
    elif args.manifest_wizard:
        validate_solc_output(args.project_dir)
        generate_custom_manifest(args.project_dir)

    # ethpm create --basic-manifest
    elif args.basic_manifest:
        validate_solc_output(args.project_dir)
        if not args.package_name:
            raise ValidationError(
                "To automatically generate a basic manifest, you must provide a --package-name."
            )

        if not args.package_version:
            raise ValidationError(
                "To automatically generate a basic manifest, you must provide a --package-version."
            )
        generate_basic_manifest(
            args.package_name, args.package_version, args.project_dir
        )
    else:
        raise InstallError(
            "To use `ethpm create` you must provide one of the following flags. "
            "--solc-input, --manifest-wizard, --basic-manifest."
        )


create_parser = ethpm_parser.add_parser(
    "create", help="Create an ethPM manifest from local smart contracts."
)
create_parser.add_argument(
    "--project-dir",
    action="store",
    dest="project_dir",
    type=Path,
    help="Path to specific project directory.",
)
create_parser.add_argument(
    "--package-name",
    dest="package_name",
    action="store",
    type=str,
    help="Package name for generating a basic manifest.",
)
create_parser.add_argument(
    "--package-version",
    dest="package_version",
    action="store",
    type=str,
    help="Package version for generating a basic manifest.",
)
add_ethpm_dir_arg_to_parser(create_parser)
create_group = create_parser.add_mutually_exclusive_group(required=True)
create_group.add_argument(
    "--manifest-wizard",
    action="store_true",
    help="Start CLI wizard for building custom manifests.",
)
create_group.add_argument(
    "--basic-manifest",
    action="store_true",
    help="Automatically generate a basic manifest for given projects dir. "
    "The generated manifest will package up all available sources and contract types.",
)
create_group.add_argument(
    "--solc-input",
    action="store_true",
    help="Generate solidity compiler standard json input for given projects dir.",
)
create_parser.set_defaults(func=create_action)


#
# ethpm scrape
#


def scrape_action(args: argparse.Namespace) -> None:
    config = Config(args)
    xdg_ethpmcli_root = get_xdg_ethpmcli_root()
    chain_data_path = xdg_ethpmcli_root / IPFS_CHAIN_DATA
    validate_chain_data_store(chain_data_path, config.w3)
    cli_logger.info("Loading IPFS scraper...")
    start_block = args.start_block if args.start_block else 0
    last_scraped_block = scrape(config.w3, xdg_ethpmcli_root, start_block)
    last_scraped_block_hash = config.w3.eth.getBlock(last_scraped_block)["hash"]
    cli_logger.info(
        "All blocks scraped up to # %d: %s.",
        last_scraped_block,
        humanize_hash(last_scraped_block_hash),
    )
    cli_logger.debug(
        "All blocks scraped up to # %d: %s.",
        last_scraped_block,
        last_scraped_block_hash,
    )


scrape_parser = ethpm_parser.add_parser(
    "scrape",
    help=(
        "Poll for VersionRelease events, scrape emitted IPFS assets "
        "and write them to local IPFS directory.",
    ),
)
scrape_parser.add_argument(
    "--ipfs-dir",
    dest="ipfs_dir",
    action="store",
    type=Path,
    help="Path to specific IPFS directory.",
)
scrape_parser.add_argument(
    "--start-block",
    dest="start_block",
    action="store",
    type=int,
    help="Block number to begin scraping from (defaults to blocks from ~ March 14, 2019).",
)
add_chain_id_arg_to_parser(scrape_parser)
scrape_parser.set_defaults(func=scrape_action)


#
# ethpm install
#


def install_action(args: argparse.Namespace) -> None:
    validate_install_cli_args(args)
    config = Config(args)
    package = Package(args.uri, args.alias, config.ipfs_backend)
    install_package(package, config)
    cli_logger.info(
        "%s package sourced from %s installed to %s.",
        package.alias,
        args.uri,
        config.ethpm_dir,
    )


install_parser = ethpm_parser.add_parser(
    "install",
    help="Install a target package, by providing its uri, to your ethPM directory.",
)
install_parser.add_argument(
    "uri",
    action="store",
    type=str,
    help="IPFS / Github / Etherscan / Registry URI of target package.",
)
install_parser.add_argument(
    "--alias", action="store", type=str, help="Alias to install target package under."
)
install_parser.add_argument(
    "--local-ipfs",
    dest="local_ipfs",
    action="store_true",
    help="Flag to use locally running IPFS node.",
)
add_ethpm_dir_arg_to_parser(install_parser)
install_parser.set_defaults(func=install_action)


#
# ethpm uninstall
#


def uninstall_action(args: argparse.Namespace) -> None:
    validate_uninstall_cli_args(args)
    config = Config(args)
    uninstall_package(args.package, config)
    cli_logger.info("%s uninstalled from %s", args.package, config.ethpm_dir)


uninstall_parser = ethpm_parser.add_parser(
    "uninstall", help="Uninstall a package from your ethPM directory."
)
uninstall_parser.add_argument(
    "package",
    action="store",
    type=str,
    help="Package name / alias of target package to uninstall.",
)
add_ethpm_dir_arg_to_parser(uninstall_parser)
uninstall_parser.set_defaults(func=uninstall_action)


#
# ethpm list
#


def list_action(args: argparse.Namespace) -> None:
    config = Config(args)
    list_installed_packages(config)


list_parser = ethpm_parser.add_parser(
    "list", help="List all installed packages in your ethPM directory."
)
add_ethpm_dir_arg_to_parser(list_parser)
list_parser.set_defaults(func=list_action)

import argparse
from pathlib import Path

from eth_utils import humanize_hash
from ethpm.constants import SUPPORTED_CHAIN_IDS

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.solc import compile_contracts, generate_solc_input
from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.commands.activate import activate_package
from ethpm_cli.commands.auth import (
    get_authorized_address,
    init_keyfile,
    link_keyfile,
    unlink_keyfile,
)
from ethpm_cli.commands.get import get_manifest
from ethpm_cli.commands.install import (
    install_package,
    list_installed_packages,
    uninstall_package,
    update_package,
)
from ethpm_cli.commands.manifest import (
    amend_manifest,
    cat_manifest,
    generate_basic_manifest,
    generate_custom_manifest,
)
from ethpm_cli.commands.package import Package
from ethpm_cli.commands.registry import (
    activate_registry,
    add_registry,
    deploy_registry,
    get_active_registry,
    list_registries,
    remove_registry,
)
from ethpm_cli.commands.release import release_package
from ethpm_cli.commands.scraper import scrape
from ethpm_cli.config import Config, validate_config_has_project_dir_attr
from ethpm_cli.constants import IPFS_CHAIN_DATA, REGISTRY_STORE, SOLC_OUTPUT
from ethpm_cli.exceptions import AuthorizationError, ConfigurationError, ValidationError
from ethpm_cli.validation import (
    validate_chain_data_store,
    validate_install_cli_args,
    validate_solc_output,
    validate_uninstall_cli_args,
)

#
# Shared args
#


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


def add_project_dir_arg_to_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-dir",
        action="store",
        dest="project_dir",
        type=Path,
        help="Path to specific project directory.",
    )


def add_keyfile_password_arg_to_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--keyfile-password",
        dest="keyfile_password",
        action="store",
        type=str,
        help="Password to local encrypted keyfile.",
    )


def add_keyfile_path_arg_to_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--keyfile-path",
        dest="keyfile_path",
        action="store",
        type=Path,
        help="Path to the keyfile you want to set as default.",
    )


def add_alias_arg_to_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--alias",
        dest="alias",
        action="store",
        type=str,
        help="Alias to use in reference to this target registry / package.",
    )


parser = argparse.ArgumentParser(description="ethpm-cli")
ethpm_parser = parser.add_subparsers(help="CLI commands", dest="command")


#
# ethpm release
#


# todo: extend to pin & release a local manifest
def release_action(args: argparse.Namespace) -> None:
    config = Config(args)
    release_package(args.package_name, args.package_version, args.manifest_uri, config)
    active_registry = get_active_registry(config.xdg_ethpmcli_root / REGISTRY_STORE)
    cli_logger.info(
        f"{args.package_name} v{args.package_version} @ {args.manifest_uri} "
        f"released to registry @ {active_registry.uri}."
    )


release_parser = ethpm_parser.add_parser(
    "release", help="Release a package on the active registry."
)
release_parser.add_argument(
    "--package-name",
    dest="package_name",
    action="store",
    type=str,
    help="Package name of package you want to release. Must match `package_name` in manifest.",
)
release_parser.add_argument(
    "--package-version",
    dest="package_version",
    action="store",
    type=str,
    help="Version of package you want to release. Must match the `version` field in manifest.",
)
release_parser.add_argument(
    "--manifest-uri",
    dest="manifest_uri",
    action="store",
    type=str,
    help="Content addressed URI at which the manifest for released package is located.",
)
add_keyfile_password_arg_to_parser(release_parser)
release_parser.set_defaults(func=release_action)


#
# ethpm auth
#


def auth_action(args: argparse.Namespace) -> None:
    Config(args)
    try:
        authorized_address = get_authorized_address()
        cli_logger.info(f"Keyfile stored for address: {authorized_address}.")
    except AuthorizationError:
        cli_logger.info(
            "No valid keyfile found. "
            "If you already have a keyfile, use `ethpm auth link --keyfile-path [path_to_keyfile]` "
            "to set your keyfile for use with ethPM CLI. \n"
            "To generate an encrypted keyfile, use `ethpm auth init`"
        )


def auth_link_action(args: argparse.Namespace) -> None:
    Config(args)
    if "keyfile_path" not in args or not args.keyfile_path:
        cli_logger.info("Invalid --keyfile-path flag")
    else:
        link_keyfile(args.keyfile_path)


def auth_unlink_action(args: argparse.Namespace) -> None:
    Config(args)
    unlink_keyfile()


def auth_init_action(args: argparse.Namespace) -> None:
    Config(args)
    init_keyfile()


auth_parser = ethpm_parser.add_parser(
    "auth", help="Authorization for automatically signing txs."
)
auth_parser.set_defaults(func=auth_action)
auth_subparsers = auth_parser.add_subparsers(dest="auth")

# ethpm auth link
auth_link_parser = auth_subparsers.add_parser(
    "link", help="Link an encrypted keyfile.",
)
add_keyfile_path_arg_to_parser(auth_link_parser)
auth_link_parser.set_defaults(func=auth_link_action)

# ethpm auth unlink
auth_unlink_parser = auth_subparsers.add_parser(
    "unlink", help="Delete the encrypted keyfile used for private key auth.",
)
auth_unlink_parser.set_defaults(func=auth_unlink_action)

# ethpm auth init
auth_init_parser = auth_subparsers.add_parser(
    "init", help="Initialize and save an encrypted keyfile for private key auth.",
)
auth_init_parser.set_defaults(func=auth_init_action)


#
# ethpm registry
#


def registry_list_action(args: argparse.Namespace) -> None:
    config = Config(args)
    list_registries(config)


def registry_add_action(args: argparse.Namespace) -> None:
    config = Config(args)
    add_registry(args.uri, args.alias, config)
    if args.alias:
        log_msg = (
            f"Registry @ {args.uri} (alias: {args.alias}) added to registry store."
        )
    else:
        log_msg = f"Registry @ {args.uri} added to registry store."
    cli_logger.info(log_msg)


def registry_activate_action(args: argparse.Namespace) -> None:
    config = Config(args)
    activate_registry(args.uri_or_alias, config)
    cli_logger.info(f"Registry @ {args.uri_or_alias} activated.")


def registry_deploy_action(args: argparse.Namespace) -> None:
    config = Config(args)
    registry_address = deploy_registry(config, args.alias)
    chain_name = SUPPORTED_CHAIN_IDS[config.w3.eth.chainId]
    explorer_uri = f"http://explorer.ethpm.com/browse/{chain_name}/{registry_address}"
    cli_logger.info(
        f"Congrats on your new ethPM registry! Check it out @ {explorer_uri}."
    )
    cli_logger.info(
        "You can now release a package on your registry with `ethpm release`."
    )


def registry_remove_action(args: argparse.Namespace) -> None:
    config = Config(args)
    remove_registry(args.uri_or_alias, config)
    cli_logger.info(f"Registry: {args.uri_or_alias} removed from registry store.")


registry_parser = ethpm_parser.add_parser("registry", help="Manage the registry store.")
registry_subparsers = registry_parser.add_subparsers(dest="registry")

# ethpm registry deploy
registry_deploy_parser = registry_subparsers.add_parser(
    "deploy",
    help="Deploy a new ERC1319 registry on the chain associated with provided chain ID.",
)
add_alias_arg_to_parser(registry_deploy_parser)
add_chain_id_arg_to_parser(registry_deploy_parser)
add_keyfile_password_arg_to_parser(registry_deploy_parser)
registry_deploy_parser.set_defaults(func=registry_deploy_action)

# ethpm registry list
registry_list_parser = registry_subparsers.add_parser(
    "list", help="List all of the available registries in registry store."
)
registry_list_parser.set_defaults(func=registry_list_action)

# ethpm registry add
registry_add_parser = registry_subparsers.add_parser(
    "add", help="Add a registry to registry store."
)
registry_add_parser.add_argument(
    "uri", action="store", type=str, help="Registry URI for target registry."
)
add_alias_arg_to_parser(registry_add_parser)
registry_add_parser.set_defaults(func=registry_add_action)

# ethpm registry remove
registry_remove_parser = registry_subparsers.add_parser(
    "remove", help="Remove a registry from the registry store."
)
registry_remove_parser.add_argument(
    "uri_or_alias", type=str, help="Registry URI or alias for registry to remove."
)
registry_remove_parser.set_defaults(func=registry_remove_action)

# ethpm registry activate
registry_activate_parser = registry_subparsers.add_parser(
    "activate",
    help="Activate a registry to be used as the default registry for releasing new packages.",
)
registry_activate_parser.add_argument(
    "uri_or_alias",
    action="store",
    type=str,
    help="Registry URI or alias for target registry.",
)
registry_activate_parser.set_defaults(func=registry_activate_action)


#
# ethpm create
#


def create_solc_input_action(args: argparse.Namespace) -> None:
    config = Config(args)
    validate_config_has_project_dir_attr(config)
    generate_solc_input(args.project_dir / "contracts")


def create_wizard_action(args: argparse.Namespace) -> None:
    config = Config(args)
    if config.project_dir and not config.manifest_path:
        if not (config.project_dir / SOLC_OUTPUT).exists():
            compile_contracts(config.project_dir)
        generate_custom_manifest(args.project_dir)
    elif config.manifest_path and not config.project_dir:
        amend_manifest(args.manifest_path)
    else:
        raise ConfigurationError(
            "Invalid project directory and/org manifest path args detected. "
            "Please only provide a project directory (to create a new manifest) "
            "or a manifest path (to amend a manifest)."
        )


def create_basic_cmd(args: argparse.Namespace) -> None:
    config = Config(args)
    validate_config_has_project_dir_attr(config)
    validate_solc_output(args.project_dir)
    if not args.package_name:
        raise ValidationError(
            "To automatically generate a basic manifest, you must provide a --package-name."
        )

    if not args.package_version:
        raise ValidationError(
            "To automatically generate a basic manifest, you must provide a --package-version."
        )
    generate_basic_manifest(args.package_name, args.package_version, args.project_dir)


create_parser = ethpm_parser.add_parser(
    "create", help="Create an ethPM manifest from local smart contracts."
)
create_subparsers = create_parser.add_subparsers(dest="create")

# ethpm create basic
create_basic_parser = create_subparsers.add_parser(
    "basic",
    help="Automatically generate a basic manifest for given projects dir. "
    "The generated manifest will package up all available sources and contract types "
    "available in the solidity compiler output found in given project directory.",
)
create_basic_parser.add_argument(
    "--package-name",
    dest="package_name",
    action="store",
    type=str,
    help="Package name for generating manifest with `basic` command.",
)
create_basic_parser.add_argument(
    "--package-version",
    dest="package_version",
    action="store",
    type=str,
    help="Package version for generating manifest with `basic` command.",
)
add_project_dir_arg_to_parser(create_basic_parser)
create_basic_parser.set_defaults(func=create_basic_cmd)

# ethpm create solc-input
create_solc_input_parser = create_subparsers.add_parser(
    "solc-input",
    help="Generate solidity compiler standard json input for given project directory.",
)
add_project_dir_arg_to_parser(create_solc_input_parser)
create_solc_input_parser.set_defaults(func=create_solc_input_action)

# ethpm create wizard
create_wizard_parser = create_subparsers.add_parser(
    "wizard",
    help="Start CLI wizard for building custom manifests from the "
    "solidity compiler output found in given project directory.",
)
create_wizard_parser.add_argument(
    "--manifest-path",
    dest="manifest_path",
    action="store",
    type=Path,
    help="Path of target manifest to amend.",
)
add_project_dir_arg_to_parser(create_wizard_parser)
create_wizard_parser.set_defaults(func=create_wizard_action)


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
    help="Poll for VersionRelease events, scrape emitted IPFS assets "
    "and write them to local IPFS directory.",
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
    package = Package(args, config.ipfs_backend)
    install_package(package, config)
    cli_logger.info(
        "%s package sourced from %s installed to %s.",
        package.alias,
        args.uri,
        config.ethpm_dir,
    )


install_parser = ethpm_parser.add_parser(
    "install", help="Install a package to a local ethPM directory."
)
install_parser.add_argument(
    "uri",
    action="store",
    type=str,
    help="IPFS / Github / Etherscan / Registry URI of target package.",
)
install_parser.add_argument(
    "--package-name",
    dest="package_name",
    action="store",
    type=str,
    help="Package name to use when installing a package from etherscan URIs.",
)
install_parser.add_argument(
    "--package-version",
    dest="package_version",
    action="store",
    type=str,
    help="Package version to use when installing a package from etherscan URIs.",
)
install_parser.add_argument(
    "--local-ipfs",
    dest="local_ipfs",
    action="store_true",
    help="Flag to use locally running IPFS node rather than defualting to Infura.",
)
add_alias_arg_to_parser(install_parser)
add_ethpm_dir_arg_to_parser(install_parser)
install_parser.set_defaults(func=install_action)

#
# ethpm update
#


def update_action(args: argparse.Namespace) -> None:
    config = Config(args)
    update_package(args, config)


update_parser = ethpm_parser.add_parser(
    "update",
    help="Update / revert a package to a different release available on active registry.",
)
update_parser.add_argument(
    "package",
    action="store",
    type=str,
    help="Package name / alias of target package to update.",
)
add_ethpm_dir_arg_to_parser(update_parser)
update_parser.set_defaults(func=update_action)


#
# ethpm uninstall
#


def uninstall_action(args: argparse.Namespace) -> None:
    validate_uninstall_cli_args(args)
    config = Config(args)
    uninstall_package(args.package, config)
    cli_logger.info("%s uninstalled from %s", args.package, config.ethpm_dir)


uninstall_parser = ethpm_parser.add_parser(
    "uninstall", help="Uninstall a package from a local ethPM directory."
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


#
# ethpm cat
#


def cat_action(args: argparse.Namespace) -> None:
    config = Config(args)
    cat_manifest(config.manifest_path)


cat_parser = ethpm_parser.add_parser(
    "cat",
    help="Preview the contents of the manifest located at the provided manifest path.",
)
cat_parser.add_argument(
    "manifest_path",
    action="store",
    type=Path,
    help="Path of target manifest to preview.",
)
cat_parser.set_defaults(func=cat_action)


#
# ethpm get
#


def get_action(args: argparse.Namespace) -> None:
    config = Config(args)
    get_manifest(args, config)


get_parser = ethpm_parser.add_parser(
    "get",
    help="Preview the contents of a manifest given a manifest URI or registry URI.",
)
get_parser.add_argument(
    "uri",
    action="store",
    type=str,
    help="Content Addressed or Registry URI of manifest to preview.",
)
get_group = get_parser.add_mutually_exclusive_group()
get_group.add_argument(
    "--output-file",
    dest="output_file",
    action="store",
    type=Path,
    help="Path target to write resolved manifest.",
)
get_group.add_argument(
    "--pretty",
    dest="pretty",
    action="store_true",
    help="Pretty print the resolved manifest JSON.",
)
get_parser.set_defaults(func=get_action, pretty=False)


#
# ethpm activate
#


def activate_action(args: argparse.Namespace) -> None:
    config = Config(args)
    activate_package(args, config)


activate_parser = ethpm_parser.add_parser(
    "activate", help="Activate a package and launch in local console.",
)
activate_parser.add_argument(
    "package_or_uri",
    action="store",
    type=str,
    help="Installed package or URI of package to activate.",
)
add_ethpm_dir_arg_to_parser(activate_parser)
add_keyfile_password_arg_to_parser(activate_parser)
activate_parser.set_defaults(func=activate_action, pretty=False)

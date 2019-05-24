import argparse
from pathlib import Path

from eth_utils import humanize_hash
from web3 import Web3
from web3.middleware import local_filter_middleware
from web3.providers.auto import load_provider_from_uri

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.config import Config
from ethpm_cli.constants import INFURA_HTTP_URI
from ethpm_cli.install import (
    install_package,
    list_installed_packages,
    uninstall_package,
)
from ethpm_cli.package import Package
from ethpm_cli.scraper import scrape
from ethpm_cli.validation import validate_install_cli_args, validate_uninstall_cli_args

parser = argparse.ArgumentParser(description="ethpm-cli")
ethpm_parser = parser.add_subparsers(help="commands", dest="command")


#
# ethpm scrape
#


def scrape_action(args: argparse.Namespace) -> None:
    w3 = Web3(load_provider_from_uri(INFURA_HTTP_URI))
    w3.middleware_onion.add(local_filter_middleware)
    ethpmcli_dir = get_xdg_ethpmcli_root()

    start_block = args.start_block if args.start_block else 0
    last_scraped_block = scrape(w3, ethpmcli_dir, start_block)
    last_scraped_block_hash = w3.eth.getBlock(last_scraped_block)["hash"]
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
    "scrape", help="Scrape for new VersionRelease events."
)
scrape_parser.add_argument(
    "--ipfs-dir",
    dest="ipfs_dir",
    action="store",
    type=Path,
    help="path to specific IPFS assets dir.",
)
scrape_parser.add_argument(
    "--start-block",
    dest="start_block",
    action="store",
    type=int,
    help="Block number to begin scraping from.",
)
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


install_parser = ethpm_parser.add_parser("install", help="Install uri")
install_parser.add_argument(
    "uri",
    action="store",
    type=str,
    help="IPFS / Github / Registry URI of package you want to install.",
)
install_parser.add_argument(
    "--ethpm-dir",
    dest="ethpm_dir",
    action="store",
    type=Path,
    help="Path to specific ethpm_packages dir.",
)
install_parser.add_argument(
    "--alias", action="store", type=str, help="Alias for installing package."
)
install_parser.add_argument(
    "--local-ipfs",
    dest="local_ipfs",
    action="store_true",
    help="Flag to use locally running IPFS node.",
)
install_parser.set_defaults(func=install_action)


#
# ethpm uninstall
#


def uninstall_action(args: argparse.Namespace) -> None:
    validate_uninstall_cli_args(args)
    config = Config(args)
    uninstall_package(args.package, config)
    cli_logger.info("%s uninstalled from %s", args.package, config.ethpm_dir)


uninstall_parser = ethpm_parser.add_parser("uninstall", help="Uninstall a package.")
uninstall_parser.add_argument(
    "package",
    action="store",
    type=str,
    help="Package name / alias of package you want to uninstall.",
)
uninstall_parser.add_argument(
    "--ethpm-dir",
    dest="ethpm_dir",
    action="store",
    type=Path,
    help="Path to specific ethpm_packages dir.",
)
uninstall_parser.set_defaults(func=uninstall_action)


#
# ethpm list
#


def list_action(args: argparse.Namespace) -> None:
    config = Config(args)
    list_installed_packages(config)


list_parser = ethpm_parser.add_parser("list", help="List installed packages")
list_parser.add_argument(
    "--ethpm-dir",
    dest="ethpm_dir",
    action="store",
    type=Path,
    help="Path to specific _ethpm_packages dir.",
)
list_parser.set_defaults(func=list_action)

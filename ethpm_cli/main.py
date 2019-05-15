import argparse
import logging
from pathlib import Path
import sys

import pkg_resources
from web3 import Web3
from web3.middleware import local_filter_middleware
from web3.providers.auto import load_provider_from_uri

from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.constants import INFURA_HTTP_URI
from ethpm_cli.install import Config, install_package, list_installed_packages
from ethpm_cli.package import Package
from ethpm_cli.scraper import scrape
from ethpm_cli.validation import validate_install_cli_args

__version__ = pkg_resources.require("ethpm-cli")[0].version


def setup_cli_logger() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def setup_scraper() -> Web3:
    w3 = Web3(load_provider_from_uri(INFURA_HTTP_URI))
    w3.middleware_onion.add(local_filter_middleware)
    return w3


def scraper(args: argparse.Namespace) -> None:
    w3 = setup_scraper()
    ethpmcli_dir = get_xdg_ethpmcli_root()
    start_block = args.start_block if args.start_block else 0
    last_scraped_block = scrape(w3, ethpmcli_dir, start_block)
    last_scraped_block_hash = w3.eth.getBlock(last_scraped_block)["hash"]
    logger = setup_cli_logger()
    logger.info(
        "All blocks scraped up to # %d: %s.",
        last_scraped_block,
        last_scraped_block_hash,
    )


def parse_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ethpm-cli")
    subparsers = parser.add_subparsers(help="commands", dest="command")

    scrape_parser = subparsers.add_parser(
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

    install_parser = subparsers.add_parser("install", help="Install uri")
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

    list_parser = subparsers.add_parser("list", help="List installed packages")
    list_parser.add_argument(
        "--ethpm-dir",
        dest="ethpm_dir",
        action="store",
        type=Path,
        help="Path to specific ethpm_packages dir.",
    )
    return parser


def main() -> None:
    logger = setup_cli_logger()
    parser = parse_arguments()
    logger.info(f"EthPM CLI v{__version__}\n")

    args = parser.parse_args()
    if args.command == "install":
        validate_install_cli_args(args)
        config = Config(args)
        package = Package(args.uri, args.alias, config.ipfs_backend)
        install_package(package, config)
        logger.info(
            "%s package sourced from %s installed to %s.",
            package.alias,
            args.uri,
            config.ethpm_dir,
        )
    elif args.command == "scrape":
        scraper(args)
    elif args.command == "list":
        config = Config(args)
        list_installed_packages(config)
    else:
        parser.error(
            "%s is an invalid command. Use `ethpmcli --help` to "
            "see the list of available commands." % args.command
        )

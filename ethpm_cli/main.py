import argparse
import logging
import sys

from eth_utils import humanize_hash
import pkg_resources
from web3 import Web3
from web3.middleware import local_filter_middleware
from web3.providers.auto import load_provider_from_uri

from ethpm_cli._utils.xdg import get_xdg_ethpmcli_root
from ethpm_cli.config import Config
from ethpm_cli.constants import INFURA_HTTP_URI
from ethpm_cli.install import (
    install_package,
    list_installed_packages,
    uninstall_package,
)
from ethpm_cli.package import Package
from ethpm_cli.parser import parser
from ethpm_cli.scraper import scrape
from ethpm_cli.validation import validate_install_cli_args, validate_uninstall_cli_args

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
        humanize_hash(last_scraped_block_hash),
    )
    logger.debug(
        "All blocks scraped up to # %d: %s.",
        last_scraped_block,
        last_scraped_block_hash,
    )


def main() -> None:
    logger = setup_cli_logger()
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
    elif args.command == "uninstall":
        validate_uninstall_cli_args(args)
        config = Config(args)
        uninstall_package(args.package, config)
        logger.info("%s uninstalled from %s", args.package, config.ethpm_dir)
    elif args.command == "scrape":
        scraper(args)
    elif args.command == "list":
        config = Config(args)
        list_installed_packages(config)
    else:
        parser.error(
            "%s is an invalid command. Use `ethpm --help` to "
            "see the list of available commands." % args.command
        )

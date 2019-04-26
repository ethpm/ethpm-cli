import argparse
import logging
from pathlib import Path
import pkg_resources
import sys

from web3 import Web3
from web3.providers.auto import load_provider_from_uri
from web3.providers.websocket import WebsocketProvider

from ethpm_cli.install import Config, install_package
from ethpm_cli.constants import INFURA_HTTP_URI, INFURA_WS_URI
from ethpm_cli.package import Package
from ethpm_cli.scraper import Scraper
from ethpm_cli.validation import validate_install_cli_args


__version__ = pkg_resources.require("ethpm-cli")[0].version


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def setup_scraper(logger, args):
    w3 = Web3(load_provider_from_uri(INFURA_HTTP_URI))
    ws_w3 = Web3(WebsocketProvider(INFURA_WS_URI, websocket_kwargs={'timeout': 60}))
    return Scraper(w3, ws_w3, content_dir = args.ipfs_dir, logger=logger) 


def scraper(logger, args):
    scraper = setup_scraper(logger, args)
    scraper.process_available_blocks()
    logger.info(f"All blocks scraped up to # {scraper.last_processed_block}.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="ethpm-cli")
    subparsers = parser.add_subparsers(help="commands", dest="command")

    scrape_parser = subparsers.add_parser("scrape", help="Scrape for new VersionRelease events.")
    scrape_parser.add_argument(
        "--ipfs-dir",
        dest="ipfs_dir",
        action="store",
        type=Path,
        help = "path to specific IPFS assets dir.",
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
    return parser.parse_args()


def main(args, logger):
    logger.info(f"EthPM CLI v{__version__}\n")

    if args.command == "install":
        validate_install_cli_args(args)
        config = Config(args)
        package = Package(args.uri, args.alias, config.ipfs_backend)
        install_package(package, config)
        logger.info(
            f"{package.alias} package sourced from {args.uri} "
            f"installed to {config.ethpm_dir}."
        )
    if args.command == "scrape":
        scraper(logger, args)
    else:
        logger.info(
            f"{args.command} is an invalid command. Use `ethpmcli --help` "
            "to see the list of available commands."
        )


if __name__ == '__main__':
    logger = get_logger()
    args = parse_arguments()
    main(args, logger)

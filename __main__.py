import argparse
import logging
import pkg_resources
import sys

from web3 import Web3
from web3.providers.auto import load_provider_from_uri
from ethpm_cli.scraper import Scraper
from web3.providers.websocket import WebsocketProvider
from pathlib import Path
from ethpm.constants import INFURA_API_KEY
from ethpm_cli.install import Config, install_package
from ethpm_cli.package import Package
from ethpm_cli.validation import validate_cli_args


__version__ = pkg_resources.require("ethpm-cli")[0].version


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def parse_arguments():
    parser = argparse.ArgumentParser(description="ethpm-cli")
    subparsers = parser.add_subparsers(help="commands", dest="command")

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
    normalize_cli_args(args)
    validate_cli_args(args)

    if args.command == "install":
        config = Config(args)
        package = Package(args.uri, args.alias, config.ipfs_backend)
        install_package(package, config)
        logger.info(
            f"{package.alias} package sourced from {args.uri} "
            f"installed to {config.ethpm_dir}."
        )
    else:
        logger.info(
            f"{args.command} is an invalid command. Use `ethpmcli --help` "
            "to see the list of available commands."
        )


def setup_scraper(content_dir=None):
    http_uri = f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'
    ws_uri = f'wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}'
    w3 = Web3(load_provider_from_uri(http_uri))
    ws_w3 = Web3(WebsocketProvider(ws_uri, websocket_kwargs={'timeout': 60}))
    return Scraper(w3, ws_w3) 

def main_ipfs():
    scraper = setup_scraper()
    while True:
        print("resolving")
        scraper.process_available_blocks()
        scraper.resolve_all_manifest_uris()


if __name__ == '__main__':
    logger = get_logger()
    args = parse_arguments()
    main(args, logger)

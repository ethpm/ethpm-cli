import argparse
from docopt import docopt
import logging
import os
import pkg_resources
import sys

from pathlib import Path
from ethpm_cli.manager import Manager
from ethpm_cli.validation import validate_cli_args


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


__version__ = pkg_resources.require("ethpm-cli")[0].version
logger.info(f"EthPM CLI v{__version__}\n")

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
    "--packages-dir",
    dest="packages_dir",
    action="store",
    type=Path,
    help="Absolute path to specific ethpm_packages dir.",
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
args = parser.parse_args()


command = args.command
if command == "install":
    validate_cli_args(args)
    manager = Manager(args.packages_dir, args.local_ipfs)
    manager.install(args.uri, args.alias)

logger.info(f"Package: {args.uri} installed.")

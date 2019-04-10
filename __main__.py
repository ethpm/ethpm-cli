from docopt import docopt
import argparse
import os
import pkg_resources

from ethpm_cli.manager import Manager

__version__ = pkg_resources.require("ethpm-cli")[0].version
print(f"EthPM CLI v{__version__}\n")

parser = argparse.ArgumentParser(description='ethpm-cli')
subparsers = parser.add_subparsers(help='commands', dest='command')

install_parser = subparsers.add_parser('install', help='Install uri')
install_parser.add_argument('uri', action='store', type=str, help='IPFS / Github / Registry URI of package you want to install')
install_parser.add_argument('-pkgs_dir', action='store', type=str, help='Path to specific ethpm_packages dir')
install_parser.add_argument('-ipfs', action='store', type=bool, help='Use locally running IPFS node')
install_parser.add_argument('-alias', action='store', type=str, help='Alias for installing package')
args = parser.parse_args()

command = args.command
if command == 'install':
    manager = Manager(args.pkgs_dir, args.ipfs)
    manager.install(args.uri, args.alias)

print(f"Package: {args.target_uri} installed to {args.pkgs_dir}")

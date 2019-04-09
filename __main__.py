from docopt import docopt
import argparse
import os
import pkg_resources

from ethpm_cli.install import install_entrypoint


__version__ = pkg_resources.require("ethpm-cli")[0].version
__doc__ = """Usage: ethpm <command> [<args>...] [options <args>]

Commands:
  install           Install an EthPM package

Options:
  -h --help         Display this message

TODO: Type 'ethpm <command> --help' for specific options and more information
about each command."""

print(f"EthPM CLI v{__version__}\n")

parser = argparse.ArgumentParser(description='ethpm-cli')
subparsers = parser.add_subparsers(help='commands', dest='command')

install_parser = subparsers.add_parser('install', help='Install uri')
install_parser.add_argument('uri', action='store', type=str, help='install ya dingus')
install_parser.add_argument('-pkgs_dir', action='store', type=str, help='pkgs dir ya dungle')
args = parser.parse_args()

command = args.command

if command == 'install':
    install_entrypoint(args)

print(args)

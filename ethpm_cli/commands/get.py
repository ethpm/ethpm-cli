import argparse
import json

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.commands.manifest import pretty_print_raw_manifest
from ethpm_cli.commands.package import Package
from ethpm_cli.config import Config
from ethpm_cli.exceptions import InstallError


def get_manifest(args: argparse.Namespace, config: Config) -> None:
    package = Package(args, config.ipfs_backend)
    manifest = json.loads(package.raw_manifest)
    if args.pretty:
        pretty_print_raw_manifest(manifest)
    elif args.output_file:
        if args.output_file.exists() or not args.output_file.parent.is_dir():
            raise InstallError(
                f"Invalid output file: {args.output_file}. Output file must not exist "
                "and live inside a valid parent directory."
            )
        args.output_file.touch()
        args.output_file.write_bytes(package.raw_manifest)
        cli_logger.info(
            f"Manifest sourced from: {args.uri} written to {args.output_file}."
        )
    else:
        cli_logger.info(manifest)

import pkg_resources

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.parser import parser

__version__ = pkg_resources.require("ethpm-cli")[0].version


def main() -> None:
    cli_logger.info(f"EthPM CLI v{__version__}\n")

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.error(
            "%s is an invalid command. Use `ethpm --help` to "
            "see the list of available commands." % args.command
        )

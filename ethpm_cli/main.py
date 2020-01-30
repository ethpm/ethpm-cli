from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.shellart import bold_green, bold_white
from ethpm_cli.constants import ETHPM_CLI_VERSION
from ethpm_cli.parser import parser

ENTRY_DESCRIPTION = "A command line tool for the Ethereum Package Manager. "


def main() -> None:
    cli_logger.info(
        f"\n{bold_white('ethPM CLI')}: {ENTRY_DESCRIPTION}v{bold_green(ETHPM_CLI_VERSION)}\n"
    )
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.error(
            "%s is an invalid command. Use `ethpm --help` to "
            "see the list of available commands." % args.command
        )

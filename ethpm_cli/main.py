from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.constants import (
    BLUE_STRING,
    COLOR_RESET,
    ETHPM_CLI_VERSION,
    GREEN_STRING,
)
from ethpm_cli.parser import parser

ETHPM_LOGO = """
       _   _     ____  __  __
   ___| |_| |__ |  _ \|  \/  |
  / _ \ __| '_ \| |_) | |\/| |
 |  __/ |_| | | |  __/| |  | |
  \___|\__|_| |_|_|   |_|  |_|

"""  # noqa: W605


def main() -> None:
    cli_logger.info(f"{BLUE_STRING}{ETHPM_LOGO}{COLOR_RESET}")
    cli_logger.info(
        "A command line tool for the Ethereum Package Manager. "
        f"{GREEN_STRING}v{ETHPM_CLI_VERSION}{COLOR_RESET}\n"
    )

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.error(
            "%s is an invalid command. Use `ethpm --help` to "
            "see the list of available commands." % args.command
        )

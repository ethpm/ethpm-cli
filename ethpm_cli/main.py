from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.constants import ETHPM_CLI_VERSION
from ethpm_cli.parser import parser

COLOR_RESET = "\x1b[0m"
ETHPM_LOGO = """
       _   _     ____  __  __
   ___| |_| |__ |  _ \|  \/  |
  / _ \ __| '_ \| |_) | |\/| |
 |  __/ |_| | | |  __/| |  | |
  \___|\__|_| |_|_|   |_|  |_|

"""  # noqa: W605


def main() -> None:
    cli_logger.info("\033[01;32m" + ETHPM_LOGO + COLOR_RESET)
    cli_logger.info(
        f"A command line tool for the Ethereum Package Manager. v{ETHPM_CLI_VERSION}\n"
    )

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.error(
            "%s is an invalid command. Use `ethpm --help` to "
            "see the list of available commands." % args.command
        )

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.constants import ETHPM_CLI_VERSION
from ethpm_cli.parser import parser


def main() -> None:
    cli_logger.info(f"ethPM CLI v{ETHPM_CLI_VERSION}\n")

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.error(
            "%s is an invalid command. Use `ethpm --help` to "
            "see the list of available commands." % args.command
        )

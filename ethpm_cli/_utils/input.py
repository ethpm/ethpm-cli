from ethpm_cli._utils.logger import cli_logger


def parse_bool_flag(question: str) -> bool:
    while True:
        response = input(f"{question} (y/n) ")
        if response.lower() == "y":
            return True
        elif response.lower() == "n":
            return False
        else:
            cli_logger.info(f"Invalid response: {response}.")
            continue

import os

from ethpm_cli.config import Config


def is_package_installed(package_name: str, config: Config) -> bool:
    return os.path.exists(config.ethpm_dir / package_name)

import os
from pathlib import Path

from ethpm_cli.exceptions import AmbigiousFileSystem


def get_home() -> Path:
    try:
        return Path.home()
    except KeyError:
        raise AmbigiousFileSystem("$HOME environment variable not set")


def get_xdg_cache_home() -> Path:
    try:
        return Path(os.environ["XDG_CACHE_HOME"])
    except KeyError:
        return get_home() / ".cache"


def get_xdg_config_home() -> Path:
    try:
        return Path(os.environ["XDG_CONFIG_HOME"])
    except KeyError:
        return get_home() / ".config"


def get_xdg_data_home() -> Path:
    try:
        return Path(os.environ["XDG_DATA_HOME"])
    except KeyError:
        return get_home() / ".local" / "share"


def get_xdg_ethpmcli_root() -> Path:
    """
    Returns the base directory under which EthPM CLI will store all data.
    """
    try:
        return Path(os.environ["XDG_ETHPMCLI_ROOT"])
    except KeyError:
        return get_xdg_data_home() / "ethpmcli"

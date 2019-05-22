from argparse import Namespace
from pathlib import Path

from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli.constants import ETHPM_DIR_NAME


class Config:
    """
    Class to manage CLI config options
    - IPFS Backend
    - Target ethpm_dir
    """

    def __init__(self, args: Namespace) -> None:
        if "local_ipfs" in args:
            self.ipfs_backend = get_ipfs_backend(args.local_ipfs)
        else:
            self.ipfs_backend = get_ipfs_backend()

        if args.ethpm_dir is None:
            self.ethpm_dir = Path.cwd() / ETHPM_DIR_NAME
            if not self.ethpm_dir.is_dir():
                self.ethpm_dir.mkdir()
        else:
            self.ethpm_dir = args.ethpm_dir

import argparse
from pathlib import Path


parser = argparse.ArgumentParser(description="ethpm-cli")
ethpm_parser = parser.add_subparsers(help="commands", dest="command")

# ethpm scrape
scrape_parser = ethpm_parser.add_parser(
    "scrape", help="Scrape for new VersionRelease events."
)
scrape_parser.add_argument(
    "--ipfs-dir",
    dest="ipfs_dir",
    action="store",
    type=Path,
    help="path to specific IPFS assets dir.",
)
scrape_parser.add_argument(
    "--start-block",
    dest="start_block",
    action="store",
    type=int,
    help="Block number to begin scraping from.",
)


# ethpm install
install_parser = ethpm_parser.add_parser("install", help="Install uri")
install_parser.add_argument(
    "uri",
    action="store",
    type=str,
    help="IPFS / Github / Registry URI of package you want to install.",
)
install_parser.add_argument(
    "--ethpm-dir",
    dest="ethpm_dir",
    action="store",
    type=Path,
    help="Path to specific ethpm_packages dir.",
)
install_parser.add_argument(
    "--alias", action="store", type=str, help="Alias for installing package."
)
install_parser.add_argument(
    "--local-ipfs",
    dest="local_ipfs",
    action="store_true",
    help="Flag to use locally running IPFS node.",
)


# ethpm uninstall
uninstall_parser = ethpm_parser.add_parser("uninstall", help="Uninstall a package.")
uninstall_parser.add_argument(
    "package",
    action="store",
    type=str,
    help="Package name / alias of package you want to uninstall.",
)
uninstall_parser.add_argument(
    "--ethpm-dir",
    dest="ethpm_dir",
    action="store",
    type=Path,
    help="Path to specific ethpm_packages dir.",
)


# ethpm list
list_parser = ethpm_parser.add_parser("list", help="List installed packages")
list_parser.add_argument(
    "--ethpm-dir",
    dest="ethpm_dir",
    action="store",
    type=Path,
    help="Path to specific _ethpm_packages dir.",
)

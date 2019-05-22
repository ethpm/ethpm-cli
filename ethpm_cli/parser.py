import argparse
from pathlib import Path


def get_ethpm_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ethpm-cli")
    subparsers = parser.add_subparsers(help="commands", dest="command")
    scrape_parser(subparsers)
    install_parser(subparsers)
    uninstall_parser(subparsers)
    list_parser(subparsers)
    return parser


def scrape_parser(subparsers: argparse._SubParsersAction) -> None:
    scrape_parser = subparsers.add_parser(
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


def install_parser(subparsers: argparse._SubParsersAction) -> None:
    install_parser = subparsers.add_parser("install", help="Install uri")
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


def uninstall_parser(subparsers: argparse._SubParsersAction) -> None:
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a package.")
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


def list_parser(subparsers: argparse._SubParsersAction) -> None:
    list_parser = subparsers.add_parser("list", help="List installed packages")
    list_parser.add_argument(
        "--ethpm-dir",
        dest="ethpm_dir",
        action="store",
        type=Path,
        help="Path to specific _ethpm_packages dir.",
    )


ETHPM_PARSER = get_ethpm_parser()

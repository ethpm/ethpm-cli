import argparse


parser = argparse.ArgumentParser(description="ethpm-cli")
subparsers = parser.add_subparsers(help="commands", dest="command")

install_parser = subparsers.add_parser("install", help="Install uri")
install_parser.add_argument("uri", action="store", type=str, help="install ya dingus")
install_parser.add_argument(
    "-pkgs_dir", action="store", type=str, help="pkgs dir ya dungle"
)
# args = parser.parse_args()

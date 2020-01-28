from argparse import Namespace
import json
from urllib import parse

from IPython import embed
from eth_utils import to_dict, to_hex
from ethpm import Package as ethpmPackage
from ethpm.exceptions import InsufficientAssetsError
from ethpm.uri import check_if_chain_matches_chain_uri
from web3.auto.infura.goerli import w3 as goerli_w3
from web3.auto.infura.kovan import w3 as kovan_w3
from web3.auto.infura.mainnet import w3 as mainnet_w3
from web3.auto.infura.rinkeby import w3 as rinkeby_w3
from web3.auto.infura.ropsten import w3 as ropsten_w3

from ethpm_cli._utils.filesystem import is_package_installed
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.commands.package import Package
from ethpm_cli.config import Config
from ethpm_cli.exceptions import InstallError, UriNotSupportedError

SUPPORTED_SCHEMES = ["http", "https", "ipfs", "etherscan", "erc1319"]

SUPPORTED_GENESIS_HASHES = {
    "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3": "mainnet",
    "0x41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d": "ropsten",
    "0x6341fd3daf94b748c72ced5a5b26028f2474f5f00d824504e4fa37a75767e177": "rinkeby",
    "0xbf7e331f7f7c1dd2e05159666b3bf8bc7a8a3a9eb1d518969eab529dd9b88c1a": "goerli",
    "0xa3c565fc15c7478862d50ccd6561e3c06b24cc509bf388941c25ea985ce32cb9": "kovan",
}


def activate_package(args: Namespace, config: Config) -> None:
    # support: etherscan / ipfs / github / erc1319
    url = parse.urlparse(args.package_or_uri)
    if url.scheme:
        if url.scheme not in SUPPORTED_SCHEMES:
            raise UriNotSupportedError(
                f"URIs with a scheme of {url.scheme} are not supported. "
                f"Currently supported schemes include: {SUPPORTED_SCHEMES}"
            )
        try:
            args.package_name = "etherscan"  # for etherscan URIs
            args.package_version = "1.0.0"  # for etherscan URIs
            args.uri = args.package_or_uri
            pkg = Package(args, config.ipfs_backend)
            manifest = pkg.manifest
        except UriNotSupportedError:
            raise UriNotSupportedError(
                f"{args.package_or_uri} is not a supported URI. The only URIs currently supported "
                "are Registry, Github Blob, Etherscan and IPFS"
            )
    else:
        if not is_package_installed(args.package_or_uri, config):
            raise InstallError(
                f"Package: {args.package_or_uri} not installed in ethPM dir: {config.ethpm_dir}."
            )
        manifest = json.loads(
            (config.ethpm_dir / args.package_or_uri / "manifest.json").read_text()
        )

    pkg = ethpmPackage(manifest, config.w3)
    cli_logger.info(f"Activating package: {pkg.name}")

    try:
        cli_logger.info(f"Found {len(pkg.contract_types)} contract types.")
        available_factories = generate_contract_factories(pkg)
    except ValueError:
        cli_logger.info(f"No contract types found.\n")
        available_factories = {}

    if "deployments" in pkg.manifest:
        available_deployments = generate_deployments(pkg)
    else:
        cli_logger.info(f"No deployments found.\n")
        available_deployments = {}

    # instantiate contract factory variables
    if len(available_factories) > 0:
        cli_logger.info("Available contract factories: ")
        for key, val in available_factories.items():
            cli_logger.info(f"- {key}_factory")
            exec(f"{key}_factory" + "=val")

    # instantiate contract instance variables
    if len(available_deployments) > 0:
        cli_logger.info("Available deployments: ")
        for key, val in available_deployments.items():
            cli_logger.info(f"- {key}")
            exec(f"{key}" + "=val")

    cli_logger.info("Starting IPython console...\n")
    embed(colors="neutral")


@to_dict
def generate_contract_factories(pkg: ethpmPackage):
    for ctype in pkg.contract_types:
        try:
            factory = pkg.get_contract_factory(ctype)
            yield ctype, factory
        except InsufficientAssetsError:
            cli_logger.info(
                f"Insufficient assets to generate factory for {ctype}. Package must contain the "
                "abi & deployment bytecode to be able to generate a factory."
            )


@to_dict
def generate_deployments(pkg: ethpmPackage):
    cli_logger.info(f"Found deployments...")
    for chain in pkg.manifest["deployments"]:
        w3, chain_name = get_matching_w3(chain)
        new_pkg = pkg.update_w3(w3)
        for dep in pkg.manifest["deployments"][chain].keys():
            yield f"{chain_name}_{dep}", new_pkg.deployments.get_instance(dep)


def get_matching_w3(chain_uri):
    all_w3s = [mainnet_w3, kovan_w3, ropsten_w3, rinkeby_w3, goerli_w3]
    for w3 in all_w3s:
        if check_if_chain_matches_chain_uri(w3, chain_uri):
            genesis = w3.eth.getBlock(0)
            chain_name = SUPPORTED_GENESIS_HASHES[to_hex(genesis["hash"])]
            return w3, chain_name
    raise InstallError(f"No valid web3 found for deployment on chain: {chain_uri}.")

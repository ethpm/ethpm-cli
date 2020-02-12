from argparse import Namespace
import json
from typing import Any, Dict, Iterable, Tuple
from urllib import parse

from IPython import embed
from eth_typing import URI
from eth_utils import to_dict, to_tuple
from ethpm import Package as ethpmPackage
from ethpm._utils.chains import parse_BIP122_uri
from ethpm.exceptions import InsufficientAssetsError
from web3 import Web3
from web3.contract import Contract

from ethpm_cli._utils.filesystem import is_package_installed
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.shellart import bold_blue, bold_green, bold_white
from ethpm_cli.commands.package import Package
from ethpm_cli.config import Config, setup_w3
from ethpm_cli.exceptions import InstallError, UriNotSupportedError

SUPPORTED_SCHEMES = ["http", "https", "ipfs", "etherscan", "erc1319", "ethpm"]

SUPPORTED_GENESIS_HASHES = {
    "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3": (
        "mainnet",
        1,
    ),
    "0x41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d": (
        "ropsten",
        3,
    ),
    "0x6341fd3daf94b748c72ced5a5b26028f2474f5f00d824504e4fa37a75767e177": (
        "rinkeby",
        4,
    ),
    "0xbf7e331f7f7c1dd2e05159666b3bf8bc7a8a3a9eb1d518969eab529dd9b88c1a": ("goerli", 5),
    "0xa3c565fc15c7478862d50ccd6561e3c06b24cc509bf388941c25ea985ce32cb9": ("kovan", 42),
}

LIGHTNING_EMOJI = "\U000026A1"
PACKAGE_EMOJI = "\U0001F4E6"


def pluralize(count: int, word: str) -> str:
    if count > 1:
        if word[-1:] == "y":
            return f"{word[:-1]}ies"
        return f"{word}s"
    else:
        return word


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
            cli_pkg = Package(args, config.ipfs_backend)
            manifest = cli_pkg.manifest
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

    activation_banner = (
        f"{(LIGHTNING_EMOJI + PACKAGE_EMOJI) * 4}{LIGHTNING_EMOJI}\n"
        f"{bold_white('Activating package')}: {bold_blue(pkg.name)}@{bold_green(pkg.version)}\n"
        f"{(LIGHTNING_EMOJI + PACKAGE_EMOJI) * 4}{LIGHTNING_EMOJI}\n"
    )
    cli_logger.info(activation_banner)

    if "contract_types" in pkg.manifest:
        num_contract_types = len(pkg.manifest["contract_types"])
    else:
        num_contract_types = 0

    if "deployments" in pkg.manifest:
        num_deployments = sum(
            len(deps) for _, deps in pkg.manifest["deployments"].items()
        )
    else:
        num_deployments = 0

    if num_contract_types > 0:
        available_factories = generate_contract_factories(pkg)
        if len(available_factories) > 0:
            formatted_factories = list_keys_for_display(available_factories)
            factories_banner = (
                f"Successfully generated {len(available_factories)} contract "
                f"{pluralize(len(available_factories), 'factory')} on mainnet from "
                f"{num_contract_types} detected contract {pluralize(num_contract_types, 'type')}.\n"
                f"{''.join(formatted_factories)}\n"
                "To get a contract factory on a different chain, call "
                f"`{bold_white('get_factory(target_factory, target_w3)')}`\n"
                "using the available contract fatories and Web3 instances.\n\n"
            )
        else:
            factories_banner = "\n"
    else:
        available_factories = {}
        factories_banner = "No detected contract types.\n"

    if num_deployments > 0:
        available_instances = generate_deployments(pkg, config)
        formatted_instances = list_keys_for_display(available_instances)
        deployments_banner = (
            f"Successfully generated {len(available_instances)} contract "
            f"{pluralize(len(available_instances), 'instance')} from {num_deployments} detected "
            f"{pluralize(num_deployments, 'deployment')}.\n"
            f"{''.join(formatted_instances)}\n"
        )
    else:
        available_instances = {}
        deployments_banner = "No detected deployments.\n"

    if config.private_key:
        auth_banner = (
            f"Deployments configured to sign for: {config.w3.eth.defaultAccount}\n"
        )
    else:
        auth_banner = (
            "Contract instances and web3 instances have not been configured with an account.\n"
            "Use the --keyfile-password flag to enable automatic signing.\n"
        )

    available_w3s = get_w3s(config)
    formatted_w3s = list_keys_for_display(available_w3s)
    web3_banner = "Available Web3 Instances\n" f"{''.join(formatted_w3s)}\n"

    banner = (
        f"{factories_banner}{deployments_banner}{web3_banner}{auth_banner}\n"
        "The API for web3.py contract factories and instances can be found here:\n"
        f"{bold_white('https://web3py.readthedocs.io/en/stable/contracts.html')}\n\n"
        "Starting IPython console... "
    )
    helper_fns = {"get_factory": get_factory}
    embed(
        user_ns={
            **available_factories,
            **available_instances,
            **available_w3s,
            **helper_fns,
        },
        banner1=banner,
        colors="neutral",
    )


def get_factory(target_factory: Contract, target_w3: Web3) -> Contract:
    return target_w3.eth.contract(
        abi=target_factory.abi, bytecode=target_factory.bytecode
    )


@to_dict
def get_w3s(config: Config) -> Iterable[Tuple[str, Web3]]:
    all_chain_data = [data for data in SUPPORTED_GENESIS_HASHES.values()]
    for name, chain_id in all_chain_data:
        w3 = setup_w3(chain_id, config.private_key)
        yield f"{name}_w3", w3


@to_tuple
def list_keys_for_display(dictionary: Dict[str, Any]) -> Iterable[str]:
    for key in dictionary.keys():
        yield f"- {bold_white(key)}\n"


@to_dict
def generate_contract_factories(pkg: ethpmPackage) -> Iterable[Tuple[str, Contract]]:
    for ctype in pkg.contract_types:
        try:
            factory = pkg.get_contract_factory(ctype)
            yield f"{ctype}_factory", factory
        except InsufficientAssetsError:
            cli_logger.info(
                f"Insufficient assets to generate factory for {ctype} "
                "(requires ABI & deployment_bytecode)."
            )


@to_dict
def generate_deployments(
    pkg: ethpmPackage, config: Config
) -> Iterable[Tuple[str, Contract]]:
    for chain in pkg.manifest["deployments"]:
        w3, chain_name = get_matching_w3(chain, config)
        new_pkg = pkg.update_w3(w3)
        for dep in pkg.manifest["deployments"][chain].keys():
            yield f"{chain_name}_{dep}", new_pkg.deployments.get_instance(dep)


def get_matching_w3(chain_uri: URI, config: Config) -> Tuple[Web3, str]:
    genesis_hash = parse_BIP122_uri(chain_uri)[0]
    chain_data = SUPPORTED_GENESIS_HASHES[genesis_hash]
    web3 = setup_w3(chain_data[1], config.private_key)
    return web3, chain_data[0]

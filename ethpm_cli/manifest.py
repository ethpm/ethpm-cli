import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from eth_typing import Manifest
from eth_utils import is_checksum_address, to_hex, to_int, to_tuple
from ethpm.constants import SUPPORTED_CHAIN_IDS
from ethpm.tools import builder as b
from ethpm.uri import create_latest_block_uri
from ethpm.validation.package import validate_package_name
from web3 import Web3

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.solc import (
    build_contract_types,
    build_sources,
    create_basic_manifest_from_solc_output,
    get_contract_types,
)
from ethpm_cli.config import get_w3
from ethpm_cli.constants import SOLC_OUTPUT
from ethpm_cli.validation import validate_solc_output


def generate_basic_manifest(package_name: str, version: str, project_dir: Path) -> None:
    manifest = create_basic_manifest_from_solc_output(
        package_name, version, project_dir
    )
    builder_fns = (b.validate(), b.write_to_disk(project_dir))
    b.build(manifest, *builder_fns)
    cli_logger.info(
        f"Manifest successfully created and written to {project_dir}/{manifest['version']}.json."
    )


def generate_custom_manifest(project_dir: Path) -> None:
    cli_logger.info("Manifest Wizard")
    cli_logger.info("---------------")
    cli_logger.info("Create ethPM manifests for local projects.")
    cli_logger.info("Project directory must include solc output.")
    cli_logger.info("Follow the steps in the docs to generate solc output.")

    contracts_dir = project_dir / "contracts"

    validate_solc_output(project_dir)
    solc_output_path = project_dir / SOLC_OUTPUT
    solc_output = json.loads(solc_output_path.read_text())["contracts"]

    builder_fns = (
        gen_package_name(),
        gen_version(),
        gen_manifest_version(),
        gen_description(),
        gen_license(),
        gen_authors(),
        gen_keywords(),
        gen_links(),
        *gen_contract_types(solc_output),
        *gen_sources(solc_output, contracts_dir),
        *gen_deployments(solc_output),
        # todo: *gen_build_dependencies(),
        # todo: ipfs pinning support
        # todo: workflow for adding a single field to existing manifest
        #   -- aka. extend existing manifest with a single deployment
        gen_validate_manifest(),
        b.write_to_disk(project_dir),
    )
    final_fns = (fn for fn in builder_fns if fn is not None)
    manifest = b.build({}, *final_fns)
    cli_logger.info(
        f"Manifest successfully created and written to {project_dir}/{manifest['version']}.json."
    )


def gen_validate_manifest() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag(
        "Would you like to validate your manifest against the json schema? (recommended)"
    )
    if flag:
        return b.validate()
    return None


def gen_contract_types(
    solc_output: Dict[str, Any]
) -> Iterable[Callable[..., Manifest]]:
    contract_types = get_contract_types(solc_output)
    pretty = "\n".join(contract_types)
    flag = parse_bool_flag(
        "\n"
        f"{len(contract_types)} contract types available.\n\n"
        f"{pretty}. \n\n"
        "Would you like to include all available contract types?"
    )
    if not flag:
        raise Exception("Custom contract types are not supported yet.")
    return build_contract_types(contract_types, solc_output)


def gen_sources(
    solc_output: Dict[str, Any], contracts_dir: Path
) -> Iterable[Callable[..., Manifest]]:
    available_sources = [
        str(src.relative_to(contracts_dir)) for src in contracts_dir.glob("**/*.sol")
    ]
    contract_types = get_contract_types(solc_output)
    pretty = "\n".join(sorted(available_sources))
    flag = parse_bool_flag(
        "\n"
        f"{len(available_sources)} sources available.\n\n"
        f"{pretty}. \n\n"
        "Would you like to include all available sources?"
    )
    if not flag:
        raise Exception("sorry, we dont support specific source selection yet.")
    inline_source_flag = parse_bool_flag(
        "Would you like to automatically inline all sources?"
    )
    if not inline_source_flag:
        raise Exception("Sorry, we dont support pinning sources yet.")
    # todo: validate a source for every contract type
    return build_sources(contract_types, solc_output, contracts_dir)


def gen_deployments(solc_output: Dict[str, Any]) -> Iterable[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add a deployment to your package?")
    if flag:
        return build_deployments(solc_output)
    return tuple()


def build_deployments(solc_output: Dict[str, Any]) -> Iterable[Callable[..., Manifest]]:
    deployments_data = gen_all_deployments(solc_output)
    return (b.deployment(**dep) for dep in deployments_data)


@to_tuple
def gen_all_deployments(solc_output: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    while True:
        yield gen_single_deployment(solc_output)
        if not parse_bool_flag("Would you like to add another deployment?"):
            break


def gen_single_deployment(solc_output: Dict[str, Any]) -> Dict[str, Any]:
    chain_id = get_chain_id()
    w3 = get_w3(chain_id)
    block_uri = create_latest_block_uri(w3)
    address = get_deployment_address()
    contract_type = get_deployment_contract_type(solc_output)
    # todo: support custom contract instance definitions
    contract_instance = contract_type
    tx_hash, block_hash = get_deployment_chain_data(w3)
    deployment_data = {
        "block_uri": block_uri,
        "contract_instance": contract_instance,
        "contract_type": contract_type,
        "address": address,
        "transaction": tx_hash,
        "block": block_hash,
    }
    return {field: value for field, value in deployment_data.items() if value}


def get_deployment_chain_data(w3: Web3) -> Tuple[Optional[str], Optional[Any]]:
    # todo: deployment_bytecode, runtime_bytecode, compiler
    flag = parse_bool_flag("Do you have a tx hash for your deployment?")
    if flag:
        tx_hash = input("Please enter your tx hash. ")
        tx = w3.eth.getTransaction(tx_hash)
        return tx_hash, to_hex(tx.blockHash)
    return (None, None)


def get_chain_id() -> int:
    question = f"On what chain ID is your deployment located? {list(SUPPORTED_CHAIN_IDS.keys())} "
    chain_id = to_int(text=input(question))
    while chain_id not in SUPPORTED_CHAIN_IDS.keys():
        cli_logger.info(f"{chain_id} is not a supported chain id. ")
        chain_id = to_int(text=input(question))
    return chain_id


def get_deployment_address() -> str:
    question = "What is the address of your deployment? "
    address = input(question)
    while not is_checksum_address(address):
        cli_logger.info(f"{address} is not a valid, checksummed address.")
        address = input(question)
    return address


def get_deployment_contract_type(solc_output: Dict[str, Any]) -> str:
    available_contract_types = get_contract_types(solc_output)
    question = (
        "What is the contract type of this deployment? \n"
        f"Available types: {available_contract_types}. \n"
    )
    contract_type = input(question)
    while contract_type not in available_contract_types:
        cli_logger.info(f"{contract_type} is not an available contract type. ")
        contract_type = input(question)
    return contract_type


def gen_package_name() -> Callable[..., Manifest]:
    package_name = input("Enter your package's name: ")
    validate_package_name(package_name)
    return b.package_name(package_name)


def gen_version() -> Callable[..., Manifest]:
    version = input("Enter your package's version: ")
    return b.version(version)


def gen_manifest_version() -> Callable[..., Manifest]:
    return b.manifest_version("2")


def gen_description() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add a description to your package?")
    if flag:
        description = input("Enter your description: ")
        return b.description(description)
    return None


def gen_license() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add a license to your package?")
    if flag:
        license = input("Enter your license: ")
        return b.license(license)
    return None


def gen_authors() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add authors to your package?")
    if flag:
        authors = input("Enter an author, or multiple authors separated by commas: ")
        return b.authors(*authors.split(","))
    return None


def gen_keywords() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add keywords to your package?")
    if flag:
        keywords = input("Enter a keyword, or multiple keywords separated by commas: ")
        return b.keywords(*keywords.split(","))
    return None


def gen_links() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag(
        "Would you like to add links to the documentation, "
        "repo, or website in your package?"
    )
    if flag:
        documentation = input(
            "Enter a link for your documentation (leave blank to skip): "
        )
        repo = input("Enter a link for your repository (leave blank to skip): ")
        website = input("Enter a link for your website (leave blank to skip): ")
        link_kwargs = {"documentation": documentation, "repo": repo, "website": website}
        actual_kwargs = {k: v for k, v in link_kwargs.items() if v}
        return b.links(**actual_kwargs)
    return None


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

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from eth_typing import Manifest
from eth_utils import is_checksum_address, to_hex, to_int, to_list, to_tuple
from ethpm.constants import SUPPORTED_CHAIN_IDS
from ethpm.tools import builder as b
from ethpm.uri import create_latest_block_uri
from ethpm.validation.manifest import validate_manifest_against_schema
from ethpm.validation.package import validate_package_name
from web3 import Web3

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.shellart import bold_blue
from ethpm_cli._utils.solc import (
    build_contract_types,
    build_inline_sources,
    build_pinned_sources,
    create_basic_manifest_from_solc_output,
    get_contract_types,
    get_contract_types_and_sources,
)
from ethpm_cli.config import setup_w3
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
    cli_logger.info(f"{bold_blue('Manifest Wizard')}")
    cli_logger.info("---------------")
    cli_logger.info("Create ethPM manifests for local projects.")

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
        *gen_contract_types_and_sources(solc_output, contracts_dir),
        *gen_deployments(solc_output),
        # todo: *gen_build_dependencies(),
        # todo: ipfs pinning support
        gen_validate_manifest(),
    )
    final_fns = (fn for fn in builder_fns if fn is not None)
    cli_logger.info(
        "Building your manifest. This could take a minute if you're pinning assets to IPFS."
    )
    manifest = b.build({}, *final_fns)
    write_manifest_to_disk(manifest, project_dir)


def amend_manifest(manifest_path: Path) -> None:
    cli_logger.info(f"{bold_blue('Manifest Wizard')}")
    cli_logger.info("---------------")
    cli_logger.info("Amend a local manifest.")
    cli_logger.info("")

    manifest = json.loads(manifest_path.read_text())
    validate_manifest_against_schema(manifest)
    pkg_repr = f"<Package {manifest['package_name']}=={manifest['version']}>"
    cli_logger.info(f"Valid manifest for {pkg_repr} found at {manifest_path}.")
    builder_fns = (
        amend_description(manifest),
        amend_license(manifest),
        amend_authors(manifest),
        amend_keywords(manifest),
        amend_links(manifest),
        *amend_deployments(manifest),
        gen_validate_manifest(),
    )
    final_fns = (fn for fn in builder_fns if fn is not None)
    amended_manifest = b.build(manifest, *final_fns)
    write_manifest_to_disk(amended_manifest, manifest_path.parent)


def amend_description(manifest: Manifest) -> Optional[Callable[..., Manifest]]:
    try:
        description = manifest["meta"]["description"]
    except KeyError:
        flag = parse_bool_flag("No description found, would you like to add one?")
    else:
        flag = parse_bool_flag(
            f"Description found ({description}). Would you like to change it?"
        )

    if flag:
        new_description = input("Enter your new description: ")
        return b.description(new_description)
    return None


def amend_license(manifest: Manifest) -> Optional[Callable[..., Manifest]]:
    try:
        license = manifest["meta"]["license"]
    except KeyError:
        flag = parse_bool_flag("No license found, would you like to add one?")
    else:
        flag = parse_bool_flag(
            f"License found ({license}). Would you like to change it?"
        )

    if flag:
        new_license = input("Enter your new license: ")
        return b.license(new_license)
    return None


def amend_authors(manifest: Manifest) -> Optional[Callable[..., Manifest]]:
    try:
        authors = manifest["meta"]["authors"]
    except KeyError:
        flag = parse_bool_flag("No authors found, would you like to add any?")
    else:
        flag = parse_bool_flag(
            f"Authors found ({authors}). Would you like to change them?"
        )

    if flag:
        new_authors = input("Enter an author or multiple authors separated by commas: ")
        return b.authors(*[author.strip() for author in new_authors.split(",")])
    return None


def amend_keywords(manifest: Manifest) -> Optional[Callable[..., Manifest]]:
    try:
        keywords = manifest["meta"]["keywords"]
    except KeyError:
        flag = parse_bool_flag("No keywords found, would you like to add any?")
    else:
        flag = parse_bool_flag(
            f"Keywords found ({keywords}). Would you like to change them?"
        )

    if flag:
        new_keywords = input(
            "Enter a keyword or multiple keywords separated by commas: "
        )
        return b.keywords(*[keyword.strip() for keyword in new_keywords.split(",")])
    return None


def amend_links(manifest: Manifest) -> Optional[Callable[..., Manifest]]:
    try:
        links = manifest["meta"]["links"]
    except KeyError:
        flag = parse_bool_flag("No links found, would you like to add any?")
    else:
        flag = parse_bool_flag(f"Links found ({links}). Would you like to change them?")

    if flag:
        documentation = input(
            "Enter a new link for your documentation (leave blank to skip): "
        )
        repo = input("Enter a new link for your repository (leave blank to skip): ")
        website = input("Enter a new link for your website (leave blank to skip): ")
        link_kwargs = {"documentation": documentation, "repo": repo, "website": website}
        actual_kwargs = {k: v for k, v in link_kwargs.items() if v}
        return b.links(**actual_kwargs)
    return None


def amend_deployments(manifest: Manifest) -> Iterable[Callable[..., Manifest]]:
    try:
        manifest["deployments"]
    except KeyError:
        flag = parse_bool_flag("No deployments found, would you like to add one?")
    else:
        # todo: support amending existing deployments, and refactor deployment strategy
        # to support multiple deployments on the same chain
        cli_logger.info(
            f"Deployments found, amending existing deployments is not currently supported."
        )
        return tuple()

    if flag:
        deployment_data = amend_single_deployment(manifest)
        return (b.deployment(**dep) for dep in deployment_data)
    return tuple()


@to_tuple
def amend_single_deployment(manifest: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    chain_id = get_chain_id()
    w3 = setup_w3(chain_id)
    block_uri = create_latest_block_uri(w3)
    address = get_deployment_address()
    available_contract_types = manifest["contract_types"].keys()
    contract_type = get_deployment_contract_type(available_contract_types)
    contract_instance = get_deployment_alias(contract_type)
    tx_hash, block_hash = get_deployment_chain_data(w3)
    deployment_data = {
        "block_uri": block_uri,
        "contract_instance": contract_instance,
        "contract_type": contract_type,
        "address": address,
        "transaction": tx_hash,
        "block": block_hash,
    }
    yield {field: value for field, value in deployment_data.items() if value}


def gen_validate_manifest() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag(
        "Would you like to validate your manifest against the json schema? (recommended)"
    )
    if flag:
        return b.validate()
    return None


def gen_contract_types_and_sources(
    solc_output: Dict[str, Any], contracts_dir: Path
) -> Tuple[Callable[..., Manifest], ...]:
    # todo: option to include additional sources not associated with included contract types
    ctypes_and_sources = get_contract_types_and_sources(solc_output)
    all_contract_types = [ctype for ctype, _ in ctypes_and_sources]
    pretty = "".join(format_contract_types_and_sources_for_display(ctypes_and_sources))
    flag = parse_bool_flag(
        "\n"
        f"{len(all_contract_types)} contract types available.\n\n"
        f"{pretty}\n"
        "Would you like to automatically include all available contract types and their sources?"
    )

    # get target contract types to include in manifest
    if flag:
        target_contract_types = all_contract_types
    else:
        while True:
            raw_included_ctypes = input(
                "Please list the contract types you would like to include, separated by commas: "
            )
            target_contract_types = [
                ct.strip(" ") for ct in raw_included_ctypes.split(",")
            ]
            invalid_contract_types = set(target_contract_types) - set(
                all_contract_types
            )
            if invalid_contract_types:
                cli_logger.info(
                    f"Invalid contract type(s) selected: {invalid_contract_types}. "
                    "Please try again."
                )
            else:
                break

    inline_source_flag = parse_bool_flag(
        "Would you like to inline source files? If not, sources will "
        "be automatically pinned to IPFS."
    )

    # generate contract types and sources builder fns for manifest builder
    generated_contract_types = build_contract_types(target_contract_types, solc_output)
    if inline_source_flag:
        generated_sources = build_inline_sources(
            target_contract_types, solc_output, contracts_dir
        )
    else:
        generated_sources = build_pinned_sources(
            target_contract_types, solc_output, contracts_dir
        )
    return ((*generated_contract_types), (*generated_sources))


@to_list
def format_contract_types_and_sources_for_display(
    ctypes_and_sources: Tuple[str],
) -> Iterable[str]:
    for ctype in sorted(ctypes_and_sources):
        yield f"{ctype[0]}\n"
        for src in sorted(ctype[1]):
            yield f"  - {src}\n"


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
    w3 = setup_w3(chain_id)
    block_uri = create_latest_block_uri(w3)
    address = get_deployment_address()
    available_contract_types = get_contract_types(solc_output)
    contract_type = get_deployment_contract_type(available_contract_types)
    contract_instance = get_deployment_alias(contract_type)
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


def get_deployment_alias(contract_type: str) -> str:
    flag = parse_bool_flag(
        "Would you like to alias your deployment? "
        f"(reference it by a name other than its contract type: {contract_type}). "
    )
    if flag:
        alias = input("Please enter your alias. ")
        validate_package_name(alias)
        return alias
    return contract_type


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


def get_deployment_contract_type(available_contract_types: Tuple[str, ...]) -> str:
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
        return b.authors(*[author.strip() for author in authors.split(",")])
    return None


def gen_keywords() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add keywords to your package?")
    if flag:
        keywords = input("Enter a keyword, or multiple keywords separated by commas: ")
        return b.keywords(*[keyword.strip() for keyword in keywords.split(",")])
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


def write_manifest_to_disk(manifest: Manifest, project_dir: Path) -> None:
    while True:
        filename = input("Please enter a filename for your manifest. ")
        filepath = project_dir / f"{filename}.json"
        if filepath.exists():
            cli_logger.info(
                f"{filepath} already exists. Please provide a different filename."
            )
            continue
        else:
            break
    filepath.touch()
    filepath.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")))
    cli_logger.info(f"Manifest successfully created and written to {filepath}.")


def cat_manifest(manifest_path: Path) -> None:
    raw_manifest = json.loads(manifest_path.read_text())
    validate_manifest_against_schema(raw_manifest)
    pretty_print_raw_manifest(raw_manifest)


def pretty_print_raw_manifest(raw_manifest: Manifest) -> None:
    manifest = ManifestDisplay(raw_manifest)
    cli_logger.info(f"Package Name: {manifest.package_name}")
    cli_logger.info(f"Package Version: {manifest.package_version}")
    cli_logger.info(f"Manifest Version: {manifest.manifest_version}\n")
    cli_logger.info(f"Metadata: \n{''.join(manifest.meta())}")
    cli_logger.info(f"Sources: \n{''.join(manifest.sources())}")
    cli_logger.info(f"Contract Types: \n{''.join(manifest.contract_types())}")
    cli_logger.info(f"Deployments: \n{''.join(manifest.deployments())}")
    cli_logger.info(f"Build Dependencies: \n{''.join(manifest.build_dependencies())}")


class ManifestDisplay:
    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest

    @property
    def package_name(self) -> str:
        return self.manifest["package_name"]

    @property
    def package_version(self) -> str:
        return self.manifest["version"]

    @property
    def manifest_version(self) -> str:
        return self.manifest["manifest_version"]

    @to_list
    def meta(self) -> Iterable[str]:
        if "meta" not in self.manifest:
            yield "None.\n"
        else:
            if "authors" in self.manifest["meta"]:
                yield f"Authors: {', '.join(self.manifest['meta']['authors'])}\n"
            if "license" in self.manifest["meta"]:
                yield f"License: {self.manifest['meta']['license']}\n"
            if "description" in self.manifest["meta"]:
                yield f"Description: {self.manifest['meta']['description']}\n"
            if "keywords" in self.manifest["meta"]:
                yield f"Keywords: {', '.join(self.manifest['meta']['keywords'])}\n"
            if "links" in self.manifest["meta"]:
                for kind, uri in self.manifest["meta"]["links"].items():
                    yield f"{kind}: {uri}\n"

    @to_list
    def sources(self) -> Iterable[str]:
        if "sources" not in self.manifest:
            yield "None.\n"
        else:
            for src, data in self.manifest["sources"].items():
                if len(data) < 50:
                    truncated = data
                else:
                    # truncate data if inlined source
                    truncated = data[:50].replace("\n", " ").replace("\r", " ")
                yield f"{src}: {truncated}\n"

    @to_list
    def contract_types(self) -> Iterable[str]:
        if "contract_types" not in self.manifest:
            yield "None.\n"
        else:
            for ct, data in self.manifest["contract_types"].items():
                yield f"{ct}:  {list(data.keys())}\n"

    @to_list
    def deployments(self) -> Iterable[str]:
        if "deployments" not in self.manifest:
            yield "None.\n"
        else:
            for chain_uri, chain_deps in self.manifest["deployments"].items():
                yield f"{chain_uri}\n"
                for alias, data in chain_deps.items():
                    yield f"- {alias} @ {data['address']} :: {data['contract_type']}\n"
                    if "transaction" in data:
                        yield f"  - tx: {data['transaction']}\n"
                    if "block" in data:
                        yield f"  - block: {data['block']}\n"

    @to_list
    def build_dependencies(self) -> Iterable[str]:
        if "build_dependencies" not in self.manifest:
            yield "None.\n"
        else:
            for pkg_name, uri in self.manifest["build_dependencies"].items():
                yield f"{pkg_name}: {uri}\n"

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

from eth_typing import Manifest
from ethpm.tools import builder as b
from ethpm.validation.package import validate_package_name

from ethpm_cli._utils.logger import cli_logger
from ethpm_cli._utils.solc import (
    build_contract_types,
    build_sources,
    create_basic_manifest_from_solc_output,
    generate_solc_input,
    get_contract_types,
)
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
    cli_logger.info("Manifest Creator")
    cli_logger.info("----------------")
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
        # todo: *gen_build_dependencies(),
        # todo: *gen_deployments,
        # todo: ipfs pinning support
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
        "Would you like to validate your manifest against the json schema? (recommended) (y/n) "
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
        f"{len(contract_types)} contract types available.\n\n"
        f"{pretty}. \n"
        "Would you like to include all available contract types? (y/n)\n"
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
        f"{len(available_sources)} sources available.\n\n"
        f"{pretty}. \n"
        "Would you like to include all available sources? (y/n)\n"
    )
    if not flag:
        raise Exception("sorry, we dont support specific source selection yet.")
    inline_source_flag = parse_bool_flag(
        "Would you like to automatically inline all sources? (y/n) "
    )
    if not inline_source_flag:
        raise Exception("Sorry, we dont support pinning sources yet.")
    # todo: validate a source for every contract type
    return build_sources(contract_types, solc_output, contracts_dir)


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
    flag = parse_bool_flag(
        "Would you like to add a description to your package? (y/n) "
    )
    if flag:
        description = input("Enter your description: ")
        return b.description(description)
    return None


def gen_license() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add a license to your package? (y/n) ")
    if flag:
        license = input("Enter your license: ")
        return b.license(license)
    return None


def gen_authors() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add authors to your package? (y/n) ")
    if flag:
        authors = input("Enter an author, or multiple authors separated by commas: ")
        return b.authors(*authors.split(","))
    return None


def gen_keywords() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag("Would you like to add keywords to your package? (y/n) ")
    if flag:
        keywords = input("Enter a keyword, or multiple keywords separated by commas: ")
        return b.keywords(*keywords.split(","))
    return None


def gen_links() -> Optional[Callable[..., Manifest]]:
    flag = parse_bool_flag(
        "Would you like to add links to the documentation, "
        "repo, or website in your package? (y/n) "
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


def generate_solc_input_for_project(project_dir: Path) -> None:
    cli_logger.info(f"No solc input file found for {project_dir.name}.")
    generate_solc_input(project_dir)


def parse_bool_flag(question: str) -> bool:
    while True:
        response = input(question)
        if response.lower() == "y":
            return True
        elif response.lower() == "n":
            return False
        else:
            cli_logger.info(f"Invalid response: {response}.")
            continue

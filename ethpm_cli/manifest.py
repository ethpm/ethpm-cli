from ethpm_cli._utils.logger import cli_logger
import json
from ethpm_cli.constants import SOLC_INPUT, SOLC_OUTPUT
from ethpm_cli._utils.solc import generate_solc_input, get_contract_types, build_contract_types, build_sources
from ethpm.tools import builder as b
from ethpm_cli.validation import validate_project_directory
from ethpm_cli._utils.solc import create_basic_manifest_from_solc_output

from pathlib import Path


def generate_basic_manifest(package_name, version, project_dir):
    manifest = create_basic_manifest_from_solc_output(package_name, version, project_dir)
    builder_fns = (
        b.validate(),
        b.write_to_disk(project_dir),
    )
    b.build(manifest, *builder_fns)
    cli_logger.info(f"Manifest successfully created and written to {project_dir}/{manifest['version']}.json.")


def generate_custom_manifest(project_dir_arg):
    cli_logger.info('Manifest Creator')
    cli_logger.info('----------------')
    cli_logger.info('Create ethPM manifests for local projects.')
    cli_logger.info('Project directory must include solc output.')
    cli_logger.info('Follow steps in docs to generate solc output.')

    project_dir = Path(project_dir_arg)
    contracts_dir = project_dir / 'contracts'

    # validate
    solc_output_path = project_dir / SOLC_OUTPUT
    if not solc_output_path.is_file():
        raise Exception

    solc_output = json.loads(solc_output_path.read_text())['contracts']

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
    cli_logger.info(f"Manifest successfully created and written to {project_dir}/{manifest['version']}.json.")


def gen_validate_manifest():
    flag = parse_bool_flag(input("Would you like to validate your manifest against the json schema? (recommended) (y/n) "))
    if flag:
        return b.validate()


def gen_contract_types(solc_output):
    contract_types = get_contract_types(solc_output)
    pretty = '\n'.join(contract_types)
    flag = parse_bool_flag(
        input(
            f"{len(contract_types)} contract types available.\n\n"
            f"{pretty}. \n"
            "Would you like to include all available contract types? (y/n)\n"
        )
    )
    if not flag:
        raise Exception("no custom contract types yet")
    return build_contract_types(contract_types, solc_output)



def gen_sources(solc_output, contracts_dir):
    available_sources = [str(src.relative_to(contracts_dir)) for src in contracts_dir.glob("**/*.sol")]
    contract_types = get_contract_types(solc_output)
    pretty = '\n'.join(available_sources)
    flag = parse_bool_flag(
        input(
            f"{len(available_sources)} sources available.\n\n"
            f"{pretty}. \n"
            "Would you like to include all available sources? (y/n)\n"
        )
    )
    if not flag:
        raise Exception('sorry, we dont support specific source selection yet.')
    inline_source_flag = parse_bool_flag(input('Would you like to automatically inline all sources? (y/n) '))
    if not inline_source_flag:
        raise Exception("sorry, we dont support pinning sources yet.")
    # todo: validate a source for every contract type
    return build_sources(contract_types, solc_output, contracts_dir)


def gen_package_name():
    package_name = input("Enter your package's name: ")
    return b.package_name(package_name)

def gen_version():
    version = input("Enter your package's version: ")
    return b.version(version)

def gen_manifest_version():
    return b.manifest_version("2")

def gen_description():
    flag = parse_bool_flag(input("Would you like to add a description to your package? (y/n) "))
    if flag:
        description = input("Enter your description: ")
        return b.description(description)

def gen_license():
    flag = parse_bool_flag(input("Would you like to add a license to your package? (y/n) "))
    if flag:
        license = input("Enter your license: ")
        return b.license(license)


def gen_authors():
    flag = parse_bool_flag(input("Would you like to add authors to your package? (y/n) "))
    if flag:
        authors = input("Enter an author, or multiple authors separated by commas: ")
        return b.authors(*authors.split(','))

def gen_keywords():
    flag = parse_bool_flag(input("Would you like to add keywords to your package? (y/n) "))
    if flag:
        keywords = input("Enter a keyword, or multiple keywords separated by commas: ")
        return b.keywords(*keywords.split(','))

def gen_links():
    flag = parse_bool_flag(input("Would you like to add links to the documentation, repo, or website in your package? (y/n) "))
    if flag:
        documentation = input("Enter a link for your documentation (leave blank to skip): ") 
        repo = input("Enter a link for your repository (leave blank to skip): ") 
        website = input("Enter a link for your website (leave blank to skip): ") 
        link_kwargs = {"documentation": documentation, "repo": repo, 'website': website}
        actual_kwargs = {k:v for k,v in link_kwargs.items() if v}
        return b.links(**actual_kwargs)

def generate_solc_input_for_project(project_dir):
    cli_logger.info(f"No solc input file found for {project_dir.name}.")
    generate_solc_input(project_dir)


def parse_bool_flag(flag):
    # todo: enhance
    # i.e. your response ('xxx') was not one of the expected response: repeat
    if flag.lower() == "y":
        return True
    return False

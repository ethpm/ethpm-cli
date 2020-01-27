import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Dict, Iterable, Tuple

from eth_typing import Manifest
from eth_utils import to_tuple
from eth_utils.toolz import assoc
from ethpm.tools import builder as b

from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.constants import SOLC_INPUT, SOLC_OUTPUT, SOLC_PATH
from ethpm_cli.exceptions import CompilationError

BASE_SOLC_INPUT = {
    "language": "Solidity",
    "settings": {
        "outputSelection": {
            "*": {
                "*": [
                    "abi",
                    "evm.bytecode.object",
                    "evm.deployedBytecode",
                    "metadata",
                    "devdoc",
                ]
            }
        }
    },
}


def generate_solc_input(contracts_dir: Path) -> None:
    sourcefiles = contracts_dir.glob("**/*.sol")
    sources = {
        str(source.relative_to(contracts_dir)): {"urls": [str(source.resolve())]}
        for source in sourcefiles
    }
    solc_output = assoc(BASE_SOLC_INPUT, "sources", sources)
    (contracts_dir.parent / SOLC_INPUT).touch()
    (contracts_dir.parent / SOLC_INPUT).write_text(json.dumps(solc_output, indent=4))
    cli_logger.info(
        "Solidity compiler input successfully created and written to %s/%s.\n",
        contracts_dir.parent,
        SOLC_INPUT,
    )


def validate_contract_directory(project_dir: Path) -> None:
    contracts_dir = project_dir / "contracts"
    contracts = [contract.name for contract in contracts_dir.glob("**/*.sol")]
    if len(contracts) == 0:
        raise CompilationError(f"No Solidity contracts found in {contracts_dir}.")
    contracts_display = "\n- ".join(contracts)
    cli_logger.info("Compiling contracts found in %s", contracts_dir)
    cli_logger.info("%d contracts found: \n- %s", len(contracts), contracts_display)


def validate_compilation_output(compiled_output: Dict[str, Any]) -> None:
    if "errors" in compiled_output:
        errors = [
            err for err in compiled_output["errors"] if err["severity"] == "error"
        ]
        warnings = [
            err for err in compiled_output["errors"] if err["severity"] == "warning"
        ]
        if errors:
            for err in errors:
                cli_logger.info(err["formattedMessage"])
            raise CompilationError("Error compiling contracts, detailed output above.")
        if warnings:
            cli_logger.info(f"{len(warnings)} warnings found in compilation.")


def find_solidity_compiler() -> str:
    if SOLC_PATH in os.environ:
        solc_path = os.environ[SOLC_PATH]
    else:
        # ignore b/c optional case is handled on 85
        solc_path = shutil.which("solc")  # type: ignore
        if not solc_path:
            raise CompilationError(
                "No solidity compiler detected, please install.\n"
                "https://solidity.readthedocs.io/en/v0.5.13/installing-solidity.html"
            )
    cli_logger.info(
        f"Solidity compiler detected at path {solc_path}, compiling contracts..."
    )
    return solc_path


def compile_contracts(project_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_project_dir = Path(tmpdir) / "project"
        shutil.copytree(project_dir, tmp_project_dir)
        tmp_solc_input_path = tmp_project_dir / SOLC_INPUT

        validate_contract_directory(project_dir)
        if not tmp_solc_input_path.is_file():
            cli_logger.info("No solidity compiler input detected...")
            generate_solc_input(tmp_project_dir / "contracts")

        solc_path = find_solidity_compiler()
        std_output = subprocess.check_output(
            [
                f"{solc_path} --standard-json --allow-paths /private{tempfile.gettempdir()} "
                f"< {tmp_solc_input_path.absolute()}"
            ],
            shell=True,
        )
        compiled_output = json.loads(std_output)
        (project_dir / SOLC_INPUT).write_text(tmp_solc_input_path.read_text())
        (project_dir / SOLC_OUTPUT).write_text(json.dumps(compiled_output))
        cli_logger.info("Contracts successfully compiled!\n")


def build_inline_sources(
    contract_types: Iterable[str], solc_output: Dict[str, Any], contracts_dir: Path
) -> Iterable[Callable[..., Manifest]]:
    return (
        b.inline_source(ctype, solc_output, contracts_dir) for ctype in contract_types
    )


def build_pinned_sources(
    contract_types: Iterable[str], solc_output: Dict[str, Any], contracts_dir: Path
) -> Iterable[Callable[..., Manifest]]:
    ipfs_backend = get_ipfs_backend()
    return (
        b.pin_source(ctype, solc_output, ipfs_backend, contracts_dir)
        for ctype in contract_types
    )


def build_contract_types(
    contract_types: Iterable[str], solc_output: Dict[str, Any]
) -> Iterable[Callable[..., Manifest]]:
    return (b.contract_type(ctype, solc_output) for ctype in contract_types)


def create_basic_manifest_from_solc_output(
    package_name: str, version: str, project_dir: Path
) -> Manifest:
    solc_output = json.loads((project_dir / SOLC_OUTPUT).read_text())["contracts"]
    contract_types = get_contract_types(solc_output)
    built_sources = build_inline_sources(
        contract_types, solc_output, project_dir / "contracts"
    )
    built_types = build_contract_types(contract_types, solc_output)
    return b.build(
        {},
        b.package_name(package_name),
        b.manifest_version("2"),
        b.version(version),
        *built_sources,
        *built_types,
        b.validate(),
    )


@to_tuple
def get_contract_types(solc_output: Dict[str, Any]) -> Iterable[str]:
    for source in solc_output:
        for ctype in solc_output[source].keys():
            yield ctype


@to_tuple
def get_contract_types_and_sources(
    solc_output: Dict[str, Any]
) -> Iterable[Tuple[str, Iterable[Path]]]:
    for source in solc_output:
        for ctype, data in solc_output[source].items():
            if data["metadata"]:
                metadata = json.loads(data["metadata"])
                sources = tuple(Path(src) for src in metadata["sources"].keys())
                yield ctype, sources
            # For Interface contracts w/ empty metadata['sources']
            else:
                yield ctype, (Path(source),)

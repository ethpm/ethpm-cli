import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Tuple

from eth_typing import Manifest
from eth_utils import to_tuple
from eth_utils.toolz import assoc
from ethpm.tools import builder as b

from ethpm_cli._utils.ipfs import get_ipfs_backend
from ethpm_cli._utils.logger import cli_logger
from ethpm_cli.constants import SOLC_INPUT, SOLC_OUTPUT

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
    cli_logger.info(
        f"Use `solc --standard-json --allow-paths {contracts_dir} "
        f"< {SOLC_INPUT} > {contracts_dir.parent / SOLC_OUTPUT}` "
        "to generate the Solidity compiler output. "
        "Requires that you have the correct Solidity compiler version installed."
    )


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
            metadata = json.loads(data["metadata"])
            sources = tuple(Path(src) for src in metadata["sources"].keys())
            yield ctype, sources

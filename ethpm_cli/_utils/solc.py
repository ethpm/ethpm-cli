import json
from pathlib import Path
from typing import Any, Dict, Iterable

from eth_typing import Manifest
from eth_utils import to_tuple
from eth_utils.toolz import assoc
from ethpm.tools import builder as b

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
    (contracts_dir.parent / SOLC_INPUT).write_text(json.dumps(solc_output))
    cli_logger.info(
        "Solidity compiler input written to %s/%s.", contracts_dir.parent, SOLC_OUTPUT
    )
    cli_logger.info(
        "Use `solc --allow-paths base_dir --standard-json < path/to/solc_input.json "
        "> path/to/solc_output.json` to generate the Solidity compiler output."
    )


def create_base_manifest_from_solc_output(
    package_name: str, version: str, project_dir: Path
) -> Manifest:
    solc_output = json.loads((project_dir / SOLC_OUTPUT).read_text())["contracts"]
    contract_types = get_contract_types(solc_output)
    built_sources = (
        b.inline_source(ctype, solc_output, (project_dir / "contracts"))
        for ctype in contract_types
    )
    built_types = (b.contract_type(ctype, solc_output) for ctype in contract_types)
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

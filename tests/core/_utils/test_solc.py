import json
import shutil

from ethpm import ASSETS_DIR

from ethpm_cli._utils.solc import (
    BASE_SOLC_INPUT,
    create_basic_manifest_from_solc_output,
    generate_solc_input,
)
from ethpm_cli.constants import SOLC_INPUT, SOLC_OUTPUT


def test_generate_solc_input(tmp_path):
    contracts_dir = tmp_path / "contracts"
    shutil.copytree(ASSETS_DIR / "registry" / "contracts", contracts_dir)
    generate_solc_input(contracts_dir)
    solc_input = json.loads((contracts_dir.parent / SOLC_INPUT).read_text())
    assert solc_input["language"] == BASE_SOLC_INPUT["language"]
    assert solc_input["settings"] == BASE_SOLC_INPUT["settings"]
    # total of 7 registry contracts
    assert len(solc_input["sources"]) == 7


def test_create_basic_manifest_from_solc_output(tmp_path):
    project_dir = tmp_path / "project"
    shutil.copytree(ASSETS_DIR / "registry", project_dir)
    (project_dir / "registry_compiler_output.json").replace(project_dir / SOLC_OUTPUT)
    actual_manifest = create_basic_manifest_from_solc_output(
        "registry", "1.0.0", project_dir
    )
    expected_manifest = json.loads((ASSETS_DIR / "registry" / "1.0.0.json").read_text())
    assert actual_manifest["package_name"] == "registry"
    assert actual_manifest["version"] == "1.0.0"
    assert actual_manifest["manifest_version"] == "2"
    assert actual_manifest["contract_types"] == expected_manifest["contract_types"]

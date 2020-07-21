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
    shutil.copytree(ASSETS_DIR / "simple-registry" / "contracts", contracts_dir)
    generate_solc_input(contracts_dir)
    solc_input = json.loads((contracts_dir.parent / SOLC_INPUT).read_text())
    assert solc_input["language"] == BASE_SOLC_INPUT["language"]
    assert solc_input["settings"] == BASE_SOLC_INPUT["settings"]
    # total of 3 registry contracts
    assert len(solc_input["sources"]) == 3


def test_create_basic_manifest_from_solc_output(tmp_path):
    project_dir = tmp_path / "project"
    shutil.copytree(ASSETS_DIR / "simple-registry", project_dir)
    (project_dir / SOLC_OUTPUT).replace(project_dir / SOLC_OUTPUT)
    actual_manifest = create_basic_manifest_from_solc_output(
        "ethpm-registry", "2.0.0a1", project_dir
    )
    expected_manifest = json.loads(
        (ASSETS_DIR / "simple-registry" / "v3.json").read_text()
    )
    assert actual_manifest["name"] == "ethpm-registry"
    assert actual_manifest["version"] == "2.0.0a1"
    assert actual_manifest["manifest"] == "ethpm/3"
    assert actual_manifest["contractTypes"] == expected_manifest["contractTypes"]

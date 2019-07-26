import shutil

from ethpm import ASSETS_DIR
import pytest

from ethpm_cli.constants import SOLC_OUTPUT


@pytest.fixture
def tmp_project_dir(tmp_path):
    tmp_project_dir = tmp_path / "registry"
    tmp_project_dir.mkdir()
    tmp_contracts_dir = tmp_project_dir / "contracts"
    shutil.copytree(ASSETS_DIR / "simple-registry" / "contracts", tmp_contracts_dir)
    shutil.copyfile(
        ASSETS_DIR / "simple-registry" / SOLC_OUTPUT, tmp_project_dir / SOLC_OUTPUT
    )
    return tmp_project_dir

import shutil

from ethpm import ASSETS_DIR
import pytest

from ethpm_cli.constants import SOLC_OUTPUT


@pytest.fixture
def tmp_project_dir(tmp_path, test_assets_dir):
    tmp_project_dir = tmp_path / "registry"
    tmp_project_dir.mkdir()
    tmp_contracts_dir = tmp_project_dir / "contracts"
    shutil.copytree(ASSETS_DIR / "simple-registry" / "contracts", tmp_contracts_dir)
    shutil.copyfile(
        ASSETS_DIR / "simple-registry" / SOLC_OUTPUT, tmp_project_dir / SOLC_OUTPUT
    )
    shutil.copyfile(
        test_assets_dir / "owned" / "1.0.0.json", tmp_project_dir / "owned.json"
    )
    shutil.copyfile(
        test_assets_dir / "dai" / "_ethpm_packages" / "dai" / "manifest.json",
        tmp_project_dir / "dai.json",
    )
    return tmp_project_dir


@pytest.fixture
def tmp_owned_dir(tmp_path, test_assets_dir):
    tmp_owned_dir = tmp_path / "owned"
    tmp_owned_dir.mkdir()
    tmp_contracts_dir = tmp_owned_dir / "contracts"
    shutil.copytree(ASSETS_DIR / "owned" / "contracts", tmp_contracts_dir)
    return tmp_owned_dir

from pathlib import Path

ETHPM_CLI_DIR = Path(__file__).parent
CLI_ASSETS_DIR: Path = ETHPM_CLI_DIR / "assets"
PROJECTS_DIR: Path = ETHPM_CLI_DIR / "projects"

from .main import main  # noqa: F401

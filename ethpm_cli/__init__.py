from pathlib import Path

CLI_ASSETS_DIR: Path = Path(__file__).parent / "assets"

from .main import main  # noqa: F401

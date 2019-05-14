from pathlib import Path

CLI_ASSETS_DIR = Path(__file__).parent / "assets"

from .main import (  # noqa: F401
    main,
)

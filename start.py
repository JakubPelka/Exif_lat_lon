from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from exif_lat_lon.cli import main as cli_main
from exif_lat_lon.gui import main as gui_main


if __name__ == "__main__":
    if len(sys.argv) == 1:
        gui_main()
    else:
        raise SystemExit(cli_main())

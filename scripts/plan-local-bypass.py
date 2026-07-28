#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "repair"))

from local_bypass_plan import main  # noqa: E402

raise SystemExit(main())


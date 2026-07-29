"""Release-candidate test package with no-delete temporary workspaces."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path


_ARCHIVE_ROOT_ENV = "WORKBUDDY_TEST_ARCHIVE_ROOT"


def _archive_root() -> Path:
    configured = os.environ.get(_ARCHIVE_ROOT_ENV)
    root = Path(configured) if configured else Path(tempfile.gettempdir()) / "pcb-prototype-quality-gate-test-archives"
    root = root.resolve()
    (root / "active").mkdir(parents=True, exist_ok=True)
    (root / "archived").mkdir(parents=True, exist_ok=True)
    return root


class ArchivedTemporaryDirectory:
    """Create a temporary directory and archive it by rename instead of deleting it."""

    def __init__(self, *, prefix: str = "case-") -> None:
        self.archive_root = _archive_root()
        self.name = tempfile.mkdtemp(prefix=prefix, dir=self.archive_root / "active")
        self._archived_path: Path | None = None

    @property
    def archived_path(self) -> Path | None:
        return self._archived_path

    def cleanup(self) -> Path | None:
        if self._archived_path is not None:
            return self._archived_path
        source = Path(self.name)
        if not source.exists():
            return None
        destination = self.archive_root / "archived" / f"{source.name}-{uuid.uuid4().hex}"
        source.rename(destination)
        self._archived_path = destination
        return destination

    def __enter__(self) -> str:
        return self.name

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cleanup()

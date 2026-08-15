import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import SETTINGS  # noqa: E402
import db  # noqa: E402


@pytest.fixture()
def db_session(tmp_path, monkeypatch):
    monkeypatch.setattr(SETTINGS, "db_path", tmp_path / "test.db")
    db.init_db()
    return db

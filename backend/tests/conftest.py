"""
Shared test setup. pytest loads this file automatically.

The test_db fixture gives EVERY test its own fresh temporary database,
so tests never touch the real data/celia.db.
"""
import pytest

import app.db as app_db
from app import tools
from db import seed


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    path = tmp_path / "test_celia.db"           # pytest creates a temp folder for us
    seed.main(path)                              # build a fresh database there
    monkeypatch.setattr(app_db, "DB_PATH", path) # point get_conn() to the temp database
    tools.PENDING_BOOKINGS.clear()               # no leftover bookings from other tests
    yield path
    tools.PENDING_BOOKINGS.clear()
import pytest

import app.db as app_db
import app.invoice as invoice
import app.reports as reports
from app import tools
from db import seed


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    path = tmp_path / "test_celia.db"
    seed.main(path)
    monkeypatch.setattr(app_db, "DB_PATH", path)
    monkeypatch.setattr(invoice, "INVOICES_DIR", tmp_path / "invoices")
    monkeypatch.setattr(reports, "REPORT_PATH", tmp_path / "reports" / "conversations.xlsx")
    tools.PENDING_BOOKINGS.clear()
    yield path
    tools.PENDING_BOOKINGS.clear()
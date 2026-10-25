"""
Tests for the admin dashboard API (app/admin.py) - password, tokens, and the
read-only data endpoints. No real LLM calls (same fake-summarizer pattern as
test_api.py).
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import admin, config, conversation_end, main, tools


@pytest.fixture
def client(test_db):
    return TestClient(main.app)


@pytest.fixture
def admin_password(monkeypatch):
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "test-pass-123")
    admin.ADMIN_TOKENS.clear()
    yield "test-pass-123"
    admin.ADMIN_TOKENS.clear()


@pytest.fixture
def admin_token(client, admin_password):
    r = client.post("/api/admin/login", json={"password": admin_password})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


PROTECTED_ENDPOINTS = [
    ("GET", "/api/admin/summary"),
    ("GET", "/api/admin/appointments"),
    ("GET", "/api/admin/conversations"),
    ("GET", "/api/admin/doctors"),
    ("GET", "/api/admin/report.xlsx"),
    ("POST", "/api/admin/logout"),
]


# ---------------- security ----------------

def test_protected_endpoints_require_token(client, test_db, admin_password):
    for method, path in PROTECTED_ENDPOINTS:
        r = client.request(method, path)
        assert r.status_code == 401, f"{method} {path} without a token"

        r2 = client.request(method, path, headers={"Authorization": "Bearer not-a-real-token"})
        assert r2.status_code == 401, f"{method} {path} with a wrong token"


def test_login_wrong_password_is_401(client, test_db, admin_password):
    r = client.post("/api/admin/login", json={"password": "wrong-password"})
    assert r.status_code == 401


def test_login_correct_password_returns_working_token(client, test_db, admin_password):
    r = client.post("/api/admin/login", json={"password": admin_password})
    assert r.status_code == 200
    body = r.json()
    assert body["expires_in_hours"] == 8

    r2 = client.get("/api/admin/summary", headers=_auth(body["token"]))
    assert r2.status_code == 200


def test_missing_admin_password_returns_503(client, test_db, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "")

    r = client.post("/api/admin/login", json={"password": "anything"})
    assert r.status_code == 503

    r2 = client.get("/api/admin/summary", headers=_auth("whatever"))
    assert r2.status_code == 503


def test_expired_token_returns_401(client, test_db, admin_token):
    admin.ADMIN_TOKENS[admin_token]["expires_at"] = datetime.now() - timedelta(seconds=1)

    r = client.get("/api/admin/summary", headers=_auth(admin_token))
    assert r.status_code == 401


def test_logout_invalidates_the_token(client, test_db, admin_token):
    r = client.post("/api/admin/logout", headers=_auth(admin_token))
    assert r.status_code == 200

    r2 = client.get("/api/admin/summary", headers=_auth(admin_token))
    assert r2.status_code == 401


# ---------------- data minimisation ----------------

def test_appointments_phone_masked_and_no_dob_or_email(client, test_db, admin_token):
    r = client.get("/api/admin/appointments", headers=_auth(admin_token))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) > 0  # db/seed.py books the first slot of every doctor

    for row in rows:
        assert "date_of_birth" not in row
        assert "email" not in row
        assert "*" in row["phone_masked"]

    demo_row = next(row for row in rows if row["patient_name"] == "Demo Patient")
    assert demo_row["phone_masked"] == "077****000"  # seeded phone is '0770000000'


def test_conversations_empty_list_when_no_excel_file(client, test_db, admin_token):
    r = client.get("/api/admin/conversations", headers=_auth(admin_token))
    assert r.status_code == 200
    assert r.json() == []


def test_conversations_rows_appear_after_saving_conversation(client, test_db, admin_token, monkeypatch):
    def fake_run_turn(session, text, debug=False):
        session.messages.append({"role": "user", "content": text})
        return "Goodbye, take care!"

    def fake_finish(session):
        return conversation_end.finish_conversation(session, summarizer=lambda s: "A fake summary.")

    monkeypatch.setattr(main, "run_turn", fake_run_turn)
    monkeypatch.setattr(main, "finish_conversation", fake_finish)

    start = client.post("/api/chat/start")
    session_id = start.json()["session_id"]
    client.post("/api/chat", json={"session_id": session_id, "message": "bye, thank you"})

    r = client.get("/api/admin/conversations", headers=_auth(admin_token))
    assert r.status_code == 200
    rows = r.json()
    found = next(row for row in rows if row["conversation_id"] == session_id)
    assert found["summary"] == "A fake summary."
    assert "date_of_birth" not in found
    assert "email" not in found


# ---------------- correctness ----------------

def test_summary_numbers_correct_after_real_booking(client, test_db, admin_token):
    before = client.get("/api/admin/summary", headers=_auth(admin_token)).json()

    doctor = tools.list_doctors()["doctors"][0]
    slot = tools.get_available_slots(doctor["doctor_id"])["slots"][0]
    prep = tools.prepare_booking(
        slot["slot_id"], "Jane Smith", "0712345678", "1990-05-15", "General checkup",
    )
    assert prep["ok"], prep
    booking = tools.confirm_booking(prep["booking_ref"])
    assert booking["ok"], booking

    after = client.get("/api/admin/summary", headers=_auth(admin_token)).json()
    assert after["total_revenue_lkr"] == before["total_revenue_lkr"] + doctor["consultation_fee"]
    assert after["upcoming_appointments"] == before["upcoming_appointments"] + 1


def test_doctors_endpoint_matches_seeded_data(client, test_db, admin_token):
    r = client.get("/api/admin/doctors", headers=_auth(admin_token))
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 7  # db/seed.py seeds exactly 7 doctors

    nimal = next(d for d in rows if d["doctor"] == "Dr. Nimal Perera")
    assert nimal["speciality"] == "Cardiology"
    assert nimal["fee"] == 4500
    assert nimal["working_days"] == "Mon,Wed,Fri"
    assert nimal["booked_slots"] == 1  # db/seed.py books each doctor's first slot
    assert nimal["free_slots"] > 0

from app import tools
from app.db import get_conn

PATIENT = dict(full_name="Jane Smith", phone="0712345678",
               date_of_birth="1990-02-15", reason="Skin rash")
OTHER_PATIENT = dict(full_name="John Perera", phone="0771234567",
                     date_of_birth="1985-07-20", reason="Check-up")


def first_free_slot(doctor_id=3):
    return tools.get_available_slots(doctor_id)["slots"][0]["slot_id"]


def slot_status(slot_id):
    with get_conn() as conn:
        return conn.execute("SELECT status FROM slots WHERE slot_id = ?", (slot_id,)).fetchone()[0]


# ---------- information tools ----------
def test_hospital_info(test_db):
    result = tools.get_hospital_info()
    assert result["ok"] is True
    assert result["hospital"]["name"] == "Lotus Care Hospital"
    assert "emergency_number" in result["hospital"]


def test_list_doctors_by_speciality(test_db):
    result = tools.list_doctors("cardiology")
    assert result["ok"] is True
    assert result["count"] == 2


def test_list_doctors_understands_cardiologist(test_db):
    assert tools.list_doctors("cardiologist")["count"] == 2


def test_unknown_speciality_returns_the_real_list(test_db):
    result = tools.list_doctors("neurology")
    assert result["ok"] is False
    assert "Cardiology" in result["available_specialities"]


def test_unknown_doctor(test_db):
    assert tools.get_doctor_details(999)["ok"] is False


def test_booked_slots_are_never_offered(test_db):          # FR4
    with get_conn() as conn:
        booked = {r[0] for r in conn.execute("SELECT slot_id FROM slots WHERE status = 'booked'")}
    for doctor_id in range(1, 8):
        offered = {s["slot_id"] for s in tools.get_available_slots(doctor_id, limit=100)["slots"]}
        assert offered.isdisjoint(booked)


# ---------- booking tools ----------
def test_invalid_details_save_nothing(test_db):            # FR7
    result = tools.prepare_booking(first_free_slot(), **{**PATIENT, "date_of_birth": "1990-02-30"})
    assert result["ok"] is False
    assert "date_of_birth" in result["field_errors"]
    assert tools.PENDING_BOOKINGS == {}


def test_prepare_does_not_book(test_db):                   # FR8: nothing saved before "yes"
    slot_id = first_free_slot()
    assert tools.prepare_booking(slot_id, **PATIENT)["ok"] is True
    assert slot_status(slot_id) == "free"


def test_full_booking(test_db):                            # FR8 + invoice row
    slot_id = first_free_slot()
    ref = tools.prepare_booking(slot_id, **PATIENT)["booking_ref"]
    result = tools.confirm_booking(ref)
    assert result["ok"] is True
    assert result["invoice_no"] == "INV-0001"
    assert result["pdf_file"] == "INV-0001_JaneSmith.pdf"
    assert slot_status(slot_id) == "booked"


def test_same_reference_cannot_be_used_twice(test_db):
    ref = tools.prepare_booking(first_free_slot(), **PATIENT)["booking_ref"]
    assert tools.confirm_booking(ref)["ok"] is True
    assert tools.confirm_booking(ref)["ok"] is False


def test_double_booking_is_impossible(test_db):            # FR8: the race situation
    slot_id = first_free_slot()
    ref1 = tools.prepare_booking(slot_id, **PATIENT)["booking_ref"]        # both prepared
    ref2 = tools.prepare_booking(slot_id, **OTHER_PATIENT)["booking_ref"]  # while still free

    assert tools.confirm_booking(ref1)["ok"] is True
    second = tools.confirm_booking(ref2)
    assert second["ok"] is False
    assert "taken" in second["error"]

    with get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) FROM appointments WHERE slot_id = ? AND status = 'booked'",
                         (slot_id,)).fetchone()[0]
    assert n == 1


def test_fake_reference_is_rejected(test_db):
    assert tools.confirm_booking("BK-FAKE123")["ok"] is False


def test_prepare_rejects_booked_slot(test_db):
    with get_conn() as conn:
        booked_slot = conn.execute(
            "SELECT slot_id FROM slots WHERE status = 'booked' LIMIT 1"
        ).fetchone()[0]

    result = tools.prepare_booking(booked_slot, **PATIENT)

    assert result["ok"] is False
    assert "already booked" in result["error"]
    assert tools.PENDING_BOOKINGS == {}      # no booking reference was created
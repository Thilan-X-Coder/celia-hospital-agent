"""
Celia's tools: plain Python functions that the LLM will call in Phase 3.

Rules:
  1. Never trust inputs - check everything.
  2. Only parameterised SQL (the ? placeholders).
  3. Always return a small dict: {"ok": True, ...} or {"ok": False, "error": ...}.
"""
import re
import sqlite3
import uuid
from datetime import date, datetime, timedelta

from app.db import get_conn
from app.validators import validate_patient
from app.invoice import build_invoice_pdf

BOOKING_REF_TTL = timedelta(minutes=15)       # a prepared booking expires after 15 minutes
PENDING_BOOKINGS: dict[str, dict] = {}        # booking_ref -> prepared booking (NOT saved yet)


class SlotTakenError(Exception):
    """Raised when a slot was booked by someone else at the last moment."""


# ---------------- small helpers ----------------
def _to_int(value) -> int | None:
    """The LLM may send "3" instead of 3. Accept both, reject garbage."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_iso_date(text: str) -> bool:
    try:
        date.fromisoformat(text)
        return len(text) == 10
    except (TypeError, ValueError):
        return False


def _is_future(slot_date: str, start_time: str) -> bool:
    return datetime.fromisoformat(f"{slot_date} {start_time}") > datetime.now()


def _safe_file_name(name: str) -> str:
    """'Jane Smith' -> 'JaneSmith' (safe for a file name)."""
    return re.sub(r"[^A-Za-z]", "", name) or "Patient"


def _remove_expired_bookings() -> None:
    now = datetime.now()
    for ref in [r for r, b in PENDING_BOOKINGS.items() if now - b["created_at"] > BOOKING_REF_TTL]:
        PENDING_BOOKINGS.pop(ref, None)


# ---------------- Tool 1: hospital information (FR2, FR5) ----------------
def get_hospital_info() -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM hospital_info WHERE id = 1").fetchone()
    if row is None:
        return {"ok": False, "error": "Hospital information is not available right now."}
    info = dict(row)
    info.pop("id", None)
    return {"ok": True, "hospital": info}


# ---------------- Tool 2: list doctors (FR3) ----------------
def list_doctors(speciality: str | None = None) -> dict:
    base_sql = """SELECT doctor_id, full_name, speciality, consultation_fee, working_days
                  FROM doctors"""
    with get_conn() as conn:
        if not speciality or not speciality.strip():
            rows = conn.execute(base_sql + " ORDER BY speciality, consultation_fee").fetchall()
        else:
            term = speciality.strip()
            # Try the full word first, then the first 6 letters
            # ("cardiologist" -> "cardio" matches "Cardiology")
            rows = []
            for search in (term, term[:6]):
                rows = conn.execute(
                    base_sql + " WHERE speciality LIKE ? ORDER BY consultation_fee",
                    (f"%{search}%",),
                ).fetchall()
                if rows:
                    break

        if not rows:
            specialities = [r[0] for r in conn.execute(
                "SELECT DISTINCT speciality FROM doctors ORDER BY speciality")]
            return {"ok": False,
                    "error": f"The hospital has no '{speciality}' doctors.",
                    "available_specialities": specialities}

    return {"ok": True, "count": len(rows), "doctors": [dict(r) for r in rows]}


# ---------------- Tool 3: doctor details (FR5) ----------------
def get_doctor_details(doctor_id) -> dict:
    doctor_id = _to_int(doctor_id)
    if doctor_id is None:
        return {"ok": False, "error": "doctor_id must be a number from list_doctors."}
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM doctors WHERE doctor_id = ?", (doctor_id,)).fetchone()
    if row is None:
        return {"ok": False, "error": f"There is no doctor with ID {doctor_id}."}
    return {"ok": True, "doctor": dict(row)}


# ---------------- Tool 4: free slots (FR4) ----------------
def get_available_slots(doctor_id, slot_date: str | None = None, limit: int = 10) -> dict:
    doctor_id = _to_int(doctor_id)
    if doctor_id is None:
        return {"ok": False, "error": "doctor_id must be a number from list_doctors."}
    if slot_date and not _is_iso_date(slot_date):
        return {"ok": False, "error": "slot_date must be in YYYY-MM-DD format."}

    sql = """SELECT slot_id, slot_date, start_time FROM slots
             WHERE doctor_id = ? AND status = 'free'
               AND datetime(slot_date || ' ' || start_time) > datetime('now', 'localtime')"""
    params: list = [doctor_id]
    if slot_date:
        sql += " AND slot_date = ?"
        params.append(slot_date)
    sql += " ORDER BY slot_date, start_time LIMIT ?"
    params.append(_to_int(limit) or 10)

    with get_conn() as conn:
        doctor = conn.execute(
            "SELECT full_name, speciality FROM doctors WHERE doctor_id = ?", (doctor_id,)
        ).fetchone()
        if doctor is None:
            return {"ok": False, "error": f"There is no doctor with ID {doctor_id}."}
        rows = conn.execute(sql, params).fetchall()

    result = {"ok": True, "doctor": doctor["full_name"],
              "speciality": doctor["speciality"], "slots": [dict(r) for r in rows]}
    if not rows:
        when = f"on {slot_date}" if slot_date else "in the next 14 days"
        result["message"] = f"No free slots {when}. Offer another date or another doctor."
    return result


# ---------------- Tool 5: validate details (FR6, FR7) ----------------
def validate_patient_details(full_name, phone, date_of_birth, reason, email=None) -> dict:
    check = validate_patient(full_name, phone, date_of_birth, reason, email)
    if check["ok"]:
        return {"ok": True, "message": "All details are valid."}
    return {"ok": False, "error": "Some details are not valid.", "field_errors": check["errors"]}


# ---------------- Tool 6: prepare booking - saves NOTHING (FR8) ----------------
def prepare_booking(slot_id, full_name, phone, date_of_birth, reason, email=None) -> dict:
    _remove_expired_bookings()

    check = validate_patient(full_name, phone, date_of_birth, reason, email)   # check again!
    if not check["ok"]:
        return {"ok": False, "error": "Some details are not valid.", "field_errors": check["errors"]}

    slot_id = _to_int(slot_id)
    if slot_id is None:
        return {"ok": False, "error": "slot_id must be a number from get_available_slots."}

    with get_conn() as conn:
        slot = conn.execute(
            """SELECT s.slot_id, s.slot_date, s.start_time, s.status,
                      d.doctor_id, d.full_name AS doctor_name, d.speciality,
                      d.consultation_fee, d.room, d.floor
               FROM slots s JOIN doctors d ON d.doctor_id = s.doctor_id
               WHERE s.slot_id = ?""", (slot_id,)
        ).fetchone()

    if slot is None:
        return {"ok": False, "error": "That time slot does not exist."}
    if slot["status"] != "free":
        return {"ok": False, "error": "That time slot is already booked. Please choose another."}
    if not _is_future(slot["slot_date"], slot["start_time"]):
        return {"ok": False, "error": "That time slot is in the past. Please choose another."}

    ref = "BK-" + uuid.uuid4().hex[:8].upper()
    PENDING_BOOKINGS[ref] = {"slot": dict(slot), "patient": check["cleaned"],
                             "created_at": datetime.now()}

    return {
        "ok": True,
        "booking_ref": ref,
        "summary": {
            "patient": check["cleaned"]["full_name"],
            "doctor": slot["doctor_name"],
            "speciality": slot["speciality"],
            "date": slot["slot_date"],
            "time": slot["start_time"],
            "fee_lkr": slot["consultation_fee"],
            "room": f"Room {slot['room']}, {slot['floor']}",
        },
        "next_step": "Read this summary to the patient and ask for a clear yes. "
                     "Call confirm_booking only after the patient says yes.",
    }


# ---------------- Tool 7: confirm booking - ONE transaction (FR8, FR9) ----------------
def _get_or_create_patient(conn, p: dict) -> int:
    row = conn.execute(
        """SELECT patient_id FROM patients
           WHERE full_name = ? AND phone = ? AND date_of_birth = ?""",
        (p["full_name"], p["phone"], p["date_of_birth"]),
    ).fetchone()
    if row:
        return row["patient_id"]
    cur = conn.execute(
        """INSERT INTO patients (full_name, phone, email, date_of_birth)
           VALUES (?, ?, ?, ?)""",
        (p["full_name"], p["phone"], p.get("email"), p["date_of_birth"]),
    )
    return cur.lastrowid


def confirm_booking(booking_ref: str) -> dict:
    _remove_expired_bookings()
    pending = PENDING_BOOKINGS.get(booking_ref)
    if pending is None:
        return {"ok": False, "error": "This booking reference is not valid, expired or "
                                      "already used. Please prepare the booking again."}

    slot, patient = pending["slot"], pending["patient"]
    try:
        with get_conn() as conn:                                   # ONE transaction
            cur = conn.execute(
                "UPDATE slots SET status = 'booked' WHERE slot_id = ? AND status = 'free'",
                (slot["slot_id"],),
            )
            if cur.rowcount == 0:                                  # someone took it first
                raise SlotTakenError()

            patient_id = _get_or_create_patient(conn, patient)
            appointment_id = conn.execute(
                """INSERT INTO appointments (patient_id, doctor_id, slot_id, reason)
                   VALUES (?, ?, ?, ?)""",
                (patient_id, slot["doctor_id"], slot["slot_id"], patient["reason"]),
            ).lastrowid

            next_no = conn.execute(
                "SELECT COALESCE(MAX(invoice_id), 0) + 1 FROM invoices").fetchone()[0]
            invoice_no = f"INV-{next_no:04d}"
            pdf_file = f"{invoice_no}_{_safe_file_name(patient['full_name'])}.pdf"
            conn.execute(
                """INSERT INTO invoices (invoice_no, appointment_id, amount, pdf_file)
                   VALUES (?, ?, ?, ?)""",
                (invoice_no, appointment_id, slot["consultation_fee"], pdf_file),
            )
    except (SlotTakenError, sqlite3.IntegrityError):
        PENDING_BOOKINGS.pop(booking_ref, None)
        return {"ok": False, "error": "Sorry, that time slot was just taken. "
                                      "Please choose another slot."}

        PENDING_BOOKINGS.pop(booking_ref, None)          # a reference can be used only once

    # The booking is saved. Now create the PDF (a file cannot be rolled back,
    # so it is created AFTER the database commit).
    invoice_ready = True
    try:
        build_invoice_pdf(invoice_no)
    except Exception:
        invoice_ready = False                        # never pretend the invoice exists

    return {
        "ok": True,
        "appointment_id": f"APT-{appointment_id:04d}",
        "invoice_no": invoice_no,
        "invoice_ready": invoice_ready,
        "pdf_file": pdf_file,
        "doctor": slot["doctor_name"],
        "speciality": slot["speciality"],
        "date": slot["slot_date"],
        "time": slot["start_time"],
        "fee_lkr": slot["consultation_fee"],
        "patient_name": patient["full_name"],
        "patient_phone": patient["phone"],
    }

# ---------------- Registry: tool name -> function (used by the agent in Phase 3) ----------------
TOOL_FUNCTIONS = {
    "get_hospital_info": get_hospital_info,
    "list_doctors": list_doctors,
    "get_doctor_details": get_doctor_details,
    "get_available_slots": get_available_slots,
    "validate_patient_details": validate_patient_details,
    "prepare_booking": prepare_booking,
    "confirm_booking": confirm_booking,
}
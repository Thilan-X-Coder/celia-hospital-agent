"""
Admin dashboard API (FR-admin): password-protected, READ-ONLY endpoints for hospital
staff. Never writes to the database or the Excel report - only SELECTs and reads files.

Patient data is personal health-related data, so responses here are minimised:
date_of_birth and email are never returned, and phone numbers are masked
(e.g. "0712345678" -> "071****678") before they leave the backend.
"""
import secrets
from datetime import date, datetime, timedelta

import openpyxl
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse

from app import config, reports
from app.api_models import (
    AdminAppointmentOut,
    AdminConversationOut,
    AdminDoctorOut,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSummaryResponse,
)
from app.db import get_conn

router = APIRouter(prefix="/api/admin", tags=["admin"])

TOKEN_TTL_HOURS = 8

# In-memory token store: {token: {"expires_at": datetime}}. Cleared on server restart,
# same trade-off as the existing in-memory SESSIONS store in app/sessions.py.
ADMIN_TOKENS: dict[str, dict] = {}


def mask_phone(phone: str) -> str:
    """'0712345678' -> '071****678'. Safe fallback for short/odd-length numbers."""
    if not phone:
        return ""
    phone = phone.strip()
    if len(phone) <= 6:
        return "*" * len(phone)
    return f"{phone[:3]}{'*' * 4}{phone[-3:]}"


def _require_configured() -> None:
    if not config.ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Admin is not configured")


def _issue_token() -> str:
    token = secrets.token_urlsafe(32)
    ADMIN_TOKENS[token] = {"expires_at": datetime.now() + timedelta(hours=TOKEN_TTL_HOURS)}
    return token


def require_admin_token(authorization: str | None = Header(default=None)) -> str:
    """Shared dependency: validates 'Authorization: Bearer <token>' on every protected route."""
    _require_configured()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin token")
    token = authorization.removeprefix("Bearer ").strip()
    entry = ADMIN_TOKENS.get(token)
    if entry is None:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    if datetime.now() >= entry["expires_at"]:
        ADMIN_TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail="Admin token expired")
    return token


def _read_conversation_rows() -> list[dict]:
    """Read the admin Excel report read-only. [] if it does not exist yet."""
    if not reports.REPORT_PATH.exists():
        return []
    try:
        wb = openpyxl.load_workbook(reports.REPORT_PATH, read_only=True, data_only=True)
        try:
            ws = wb[reports.SHEET]
            header = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
            rows = []
            for values in ws.iter_rows(min_row=2, values_only=True):
                if values[0] is None:  # skip blank trailing rows
                    continue
                rows.append(dict(zip(header, values)))
            return rows
        finally:
            wb.close()
    except PermissionError:
        raise HTTPException(
            status_code=503,
            detail="The Excel report is open in another program. Close it and try again.",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Could not read the conversation report")


def _conversation_stats() -> tuple[int, int]:
    rows = _read_conversation_rows()
    total = len(rows)
    booked = len([r for r in rows if r.get("Booking Status") == "Booked"])
    return total, booked


# ---------------- security ----------------

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(body: AdminLoginRequest):
    _require_configured()
    if not secrets.compare_digest(body.password, config.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = _issue_token()
    return AdminLoginResponse(token=token, expires_in_hours=TOKEN_TTL_HOURS)


@router.post("/logout")
def admin_logout(token: str = Depends(require_admin_token)):
    ADMIN_TOKENS.pop(token, None)
    return {"ok": True}


# ---------------- data (read-only) ----------------

@router.get("/summary", response_model=AdminSummaryResponse)
def admin_summary(_: str = Depends(require_admin_token)):
    today = date.today().isoformat()
    total_conversations, booked_conversations = _conversation_stats()
    conversion_rate = (booked_conversations / total_conversations) if total_conversations else 0.0

    with get_conn() as conn:
        todays_appointments = conn.execute(
            """
            SELECT COUNT(*) FROM appointments a JOIN slots s ON a.slot_id = s.slot_id
            WHERE a.status = 'booked' AND s.slot_date = ?
            """,
            (today,),
        ).fetchone()[0]
        upcoming_appointments = conn.execute(
            """
            SELECT COUNT(*) FROM appointments a JOIN slots s ON a.slot_id = s.slot_id
            WHERE a.status = 'booked' AND s.slot_date >= ?
            """,
            (today,),
        ).fetchone()[0]
        total_revenue_lkr = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices").fetchone()[0]

    return AdminSummaryResponse(
        total_conversations=total_conversations,
        booked_conversations=booked_conversations,
        conversion_rate=conversion_rate,
        todays_appointments=todays_appointments,
        total_revenue_lkr=total_revenue_lkr,
        upcoming_appointments=upcoming_appointments,
    )


@router.get("/appointments", response_model=list[AdminAppointmentOut])
def admin_appointments(_: str = Depends(require_admin_token)):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT a.appointment_id, a.status, a.reason,
                   p.full_name AS patient_name, p.phone AS phone,
                   d.full_name AS doctor, d.speciality AS speciality,
                   s.slot_date AS date, s.start_time AS time,
                   i.invoice_no AS invoice_no, i.pdf_file AS pdf_file
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            JOIN slots s ON a.slot_id = s.slot_id
            LEFT JOIN invoices i ON i.appointment_id = a.appointment_id
            ORDER BY s.slot_date DESC, s.start_time DESC
            """
        ).fetchall()

    return [
        AdminAppointmentOut(
            appointment_id=f"APT-{row['appointment_id']:04d}",
            patient_name=row["patient_name"],
            phone_masked=mask_phone(row["phone"]),
            doctor=row["doctor"],
            speciality=row["speciality"],
            date=row["date"],
            time=row["time"],
            status=row["status"],
            reason=row["reason"],
            invoice_no=row["invoice_no"],
            invoice_url=f"/invoices/{row['pdf_file']}" if row["pdf_file"] else None,
        )
        for row in rows
    ]


@router.get("/conversations", response_model=list[AdminConversationOut])
def admin_conversations(_: str = Depends(require_admin_token)):
    rows = _read_conversation_rows()
    return [
        AdminConversationOut(
            conversation_id=r.get("Conversation ID"),
            date=r.get("Date"),
            time=r.get("Time"),
            patient_name=r.get("Patient Name"),
            phone_masked=mask_phone(r.get("Phone") or ""),
            topics=r.get("Topics"),
            booking_status=r.get("Booking Status"),
            doctor=r.get("Doctor"),
            speciality=r.get("Speciality"),
            appointment_date=r.get("Appointment Date"),
            appointment_time=r.get("Appointment Time"),
            invoice_no=r.get("Invoice No"),
            summary=r.get("Summary"),
        )
        for r in rows
    ]


@router.get("/doctors", response_model=list[AdminDoctorOut])
def admin_doctors(_: str = Depends(require_admin_token)):
    today = date.today().isoformat()
    with get_conn() as conn:
        doctors = conn.execute(
            "SELECT doctor_id, full_name, speciality, consultation_fee, working_days FROM doctors"
        ).fetchall()
        out = []
        for d in doctors:
            free_slots = conn.execute(
                "SELECT COUNT(*) FROM slots WHERE doctor_id = ? AND slot_date >= ? AND status = 'free'",
                (d["doctor_id"], today),
            ).fetchone()[0]
            booked_slots = conn.execute(
                "SELECT COUNT(*) FROM slots WHERE doctor_id = ? AND slot_date >= ? AND status = 'booked'",
                (d["doctor_id"], today),
            ).fetchone()[0]
            out.append(
                AdminDoctorOut(
                    doctor=d["full_name"],
                    speciality=d["speciality"],
                    fee=d["consultation_fee"],
                    working_days=d["working_days"],
                    free_slots=free_slots,
                    booked_slots=booked_slots,
                )
            )
    return out


@router.get("/report.xlsx")
def admin_download_report(_: str = Depends(require_admin_token)):
    if not reports.REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="No report file yet")
    return FileResponse(
        reports.REPORT_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="conversations.xlsx",
    )

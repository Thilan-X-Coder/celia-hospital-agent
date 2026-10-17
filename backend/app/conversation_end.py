"""
Ends a conversation: builds the Excel row from REAL session data and saves it.
"""
from app import reports
from app.sessions import Session
from app.summary import fallback_summary, make_summary

TOPIC_NAMES = {
    "get_hospital_info": "Hospital info",
    "list_doctors": "Doctors",
    "get_doctor_details": "Doctor details",
    "get_available_slots": "Availability",
    "validate_patient_details": "Booking",
    "prepare_booking": "Booking",
    "confirm_booking": "Booking",
}


def topics_from_tools(tools_used: list) -> str:
    topics = []
    for name in tools_used:
        topic = TOPIC_NAMES.get(name)
        if topic and topic not in topics:
            topics.append(topic)
    return ", ".join(topics) or "General chat"


def finish_conversation(session: Session, summarizer=make_summary) -> dict:
    """Save ONE row for this conversation. Safe to call more than once."""
    if session.summary_saved:
        return {"ok": True, "message": "Already saved.", "summary": None}

    if not any(m["role"] == "user" for m in session.messages):
        summary = "The patient opened the chat but did not ask anything."
    else:
        try:
            summary = summarizer(session)
        except Exception:
            summary = fallback_summary(session)

    b = session.booking or {}
    p = session.patient or {}
    row = {
        "Conversation ID": session.session_id,
        "Date": session.started_at.strftime("%Y-%m-%d"),
        "Time": session.started_at.strftime("%H:%M"),
        "Patient Name": p.get("full_name", ""),
        "Phone": p.get("phone", ""),
        "Topics": topics_from_tools(session.tools_used),
        "Booking Status": "Booked" if b else "Not booked",
        "Doctor": b.get("doctor", ""),
        "Speciality": b.get("speciality", ""),
        "Appointment Date": b.get("date", ""),
        "Appointment Time": b.get("time", ""),
        "Invoice No": b.get("invoice_no", ""),
        "Summary": summary,
    }
    result = reports.append_conversation_row(row)
    if result["ok"]:
        session.summary_saved = True
    result["summary"] = summary
    return result
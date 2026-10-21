"""
FastAPI layer for Celia. Only wires up existing app/ modules - the LLM/tool/DB
logic itself lives in agent.py, tools.py, invoice.py, conversation_end.py, etc.
"""
import asyncio
import contextlib
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.agent import is_goodbye, run_turn
from app.api_models import (
    BookingOut,
    ChatEndRequest,
    ChatEndResponse,
    ChatRequest,
    ChatResponse,
    ChatStartResponse,
    HealthResponse,
    HospitalResponse,
    PendingBookingOut,
)
from app.conversation_end import finish_conversation
from app.llm_client import provider_info
from app.prompts import greeting
from app.sessions import SESSIONS, create_session, get_session
from app.tools import get_hospital_info
from app import tools
import app.invoice as invoice

SWEEP_INTERVAL_SECONDS = 60
BOOKED_IDLE_MINUTES = 3    # session.booking is not None
IDLE_MINUTES = 10          # everything else (info-only or an unfinished booking)

_finish_lock = threading.Lock()


def _finish_with_lock(session) -> dict:
    with _finish_lock:
        return finish_conversation(session)


def sweep_inactive_sessions(now: datetime) -> list[str]:
    """Save any session that has gone quiet. Returns the session_ids it actually saved."""
    saved = []
    for session in list(SESSIONS.values()):
        if session.summary_saved:
            continue
        if not any(m["role"] == "user" for m in session.messages):
            continue
        idle_minutes = BOOKED_IDLE_MINUTES if session.booking is not None else IDLE_MINUTES
        cutoff = now - timedelta(minutes=idle_minutes)
        if session.last_activity > cutoff:
            continue
        try:
            result = _finish_with_lock(session)
        except Exception:
            continue  # one bad session must not stop the rest of the sweep
        if result.get("ok"):
            saved.append(session.session_id)
    return saved


def _save_all_unsaved():
    for session in list(SESSIONS.values()):
        if session.summary_saved:
            continue
        if any(m["role"] == "user" for m in session.messages):
            try:
                _finish_with_lock(session)
            except Exception:
                continue


async def _sweeper_loop():
    while True:
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
        await asyncio.to_thread(sweep_inactive_sessions, datetime.now())


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sweeper_loop())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    await asyncio.to_thread(_save_all_unsaved)


app = FastAPI(title="Celia API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", model=provider_info())


@app.get("/api/hospital", response_model=HospitalResponse)
def hospital():
    info = get_hospital_info()["hospital"]
    return HospitalResponse(**info)


@app.post("/api/chat/start", response_model=ChatStartResponse)
def chat_start():
    session = create_session()
    hello = greeting()
    session.messages.append({"role": "assistant", "content": hello})
    return ChatStartResponse(session_id=session.session_id, greeting=hello)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session = get_session(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    session.last_activity = datetime.now()
    prev_booking = session.booking
    reply = run_turn(session, req.message, debug=False)
    ended = is_goodbye(req.message)
    if ended:
        _finish_with_lock(session)   # server guarantees the save; idempotent

    booking_out = None
    invoice_url = None
    if session.booking is not None and session.booking is not prev_booking:
        b = session.booking
        booking_out = BookingOut(
            appointment_id=b["appointment_id"],
            invoice_no=b["invoice_no"],
            doctor=b["doctor"],
            speciality=b["speciality"],
            date=b["date"],
            time=b["time"],
            fee_lkr=b["fee_lkr"],
        )
        if b.get("invoice_ready"):
            invoice_url = f"/invoices/{b['pdf_file']}"

    pending_booking_out = None
    for ref, turn in session.pending_refs.items():
        if turn == session.turn_no:
            data = tools.PENDING_BOOKINGS.get(ref)
            if data:
                slot, patient = data["slot"], data["patient"]
                pending_booking_out = PendingBookingOut(
                    patient_name=patient["full_name"],
                    doctor=slot["doctor_name"],
                    speciality=slot["speciality"],
                    date=slot["slot_date"],
                    time=slot["start_time"],
                    fee_lkr=slot["consultation_fee"],
                    room=f"Room {slot['room']}, {slot['floor']}",
                )

    return ChatResponse(
        reply=reply,
        booking=booking_out,
        invoice_url=invoice_url,
        conversation_ended=ended,
        pending_booking=pending_booking_out,
    )


@app.post("/api/chat/end", response_model=ChatEndResponse)
def chat_end(req: ChatEndRequest):
    session = get_session(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    result = _finish_with_lock(session)   # idempotent: safe even if already saved
    return ChatEndResponse(saved=result["ok"], summary=result.get("summary"))


@app.get("/invoices/{file}")
def get_invoice(file: str):
    if not file.endswith(".pdf") or "/" in file or "\\" in file or ".." in file:
        raise HTTPException(status_code=400, detail="Invalid file name")

    path = invoice.INVOICES_DIR / file
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Invoice not found")

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=file,
        content_disposition_type="inline",
    )

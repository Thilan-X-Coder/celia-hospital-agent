"""
FastAPI layer for Celia. Only wires up existing app/ modules - the LLM/tool/DB
logic itself lives in agent.py, tools.py, invoice.py, conversation_end.py, etc.
"""
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
)
from app.conversation_end import finish_conversation
from app.llm_client import provider_info
from app.prompts import greeting
from app.sessions import create_session, get_session
from app.tools import get_hospital_info
import app.invoice as invoice

app = FastAPI(title="Celia API")

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

    prev_booking = session.booking
    reply = run_turn(session, req.message, debug=False)
    ended = is_goodbye(req.message)
    if ended:
        finish_conversation(session)   # server guarantees the save; idempotent

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

    return ChatResponse(
        reply=reply,
        booking=booking_out,
        invoice_url=invoice_url,
        conversation_ended=ended,
    )


@app.post("/api/chat/end", response_model=ChatEndResponse)
def chat_end(req: ChatEndRequest):
    session = get_session(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    result = finish_conversation(session)   # idempotent: safe even if already saved
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

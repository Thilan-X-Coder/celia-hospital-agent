"""
Request/response shapes for the FastAPI layer (app/main.py).
Kept in their own file so the HTTP "contract" is easy to find in one place.
"""
from typing import Optional

from pydantic import BaseModel, field_validator


class HealthResponse(BaseModel):
    status: str
    model: str


class HospitalResponse(BaseModel):
    name: str
    phone: str
    emergency_number: str


class ChatStartResponse(BaseModel):
    session_id: str
    greeting: str


class ChatRequest(BaseModel):
    session_id: str
    message: str

    @field_validator("message")
    @classmethod
    def message_must_be_1_to_1000_chars_after_strip(cls, v: str) -> str:
        cleaned = v.strip()
        if not (1 <= len(cleaned) <= 1000):
            raise ValueError("message must be 1-1000 characters after trimming whitespace")
        return cleaned


class BookingOut(BaseModel):
    appointment_id: str
    invoice_no: str
    doctor: str
    speciality: str
    date: str
    time: str
    fee_lkr: float


class ChatResponse(BaseModel):
    reply: str
    booking: Optional[BookingOut] = None
    invoice_url: Optional[str] = None
    conversation_ended: bool


class ChatEndRequest(BaseModel):
    session_id: str


class ChatEndResponse(BaseModel):
    saved: bool
    summary: Optional[str] = None

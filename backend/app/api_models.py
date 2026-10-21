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
    address: str
    phone: str
    email: Optional[str] = None
    emergency_number: str
    opening_hours: Optional[str] = None
    visiting_hours: Optional[str] = None
    departments: Optional[str] = None
    facilities: Optional[str] = None
    what_to_bring: Optional[str] = None
    payment_methods: Optional[str] = None


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


class PendingBookingOut(BaseModel):
    patient_name: str
    doctor: str
    speciality: str
    date: str
    time: str
    fee_lkr: float
    room: str


class ChatResponse(BaseModel):
    reply: str
    booking: Optional[BookingOut] = None
    invoice_url: Optional[str] = None
    conversation_ended: bool
    pending_booking: Optional[PendingBookingOut] = None


class ChatEndRequest(BaseModel):
    session_id: str


class ChatEndResponse(BaseModel):
    saved: bool
    summary: Optional[str] = None

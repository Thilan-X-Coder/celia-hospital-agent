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


# --- Admin dashboard models (read-only, password-protected) ---

class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    expires_in_hours: int


class AdminSummaryResponse(BaseModel):
    total_conversations: int
    booked_conversations: int
    conversion_rate: float
    todays_appointments: int
    total_revenue_lkr: float
    upcoming_appointments: int


class AdminAppointmentOut(BaseModel):
    appointment_id: str
    patient_name: str
    phone_masked: str
    doctor: str
    speciality: str
    date: str
    time: str
    status: str
    reason: Optional[str] = None
    invoice_no: Optional[str] = None
    invoice_url: Optional[str] = None


class AdminConversationOut(BaseModel):
    conversation_id: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    patient_name: Optional[str] = None
    phone_masked: Optional[str] = None
    topics: Optional[str] = None
    booking_status: Optional[str] = None
    doctor: Optional[str] = None
    speciality: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    invoice_no: Optional[str] = None
    summary: Optional[str] = None


class AdminDoctorOut(BaseModel):
    doctor: str
    speciality: str
    fee: float
    working_days: str
    free_slots: int
    booked_slots: int

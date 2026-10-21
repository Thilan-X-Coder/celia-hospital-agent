"""
Conversation memory. One Session per chat.
Stored in memory (a dict) - fine for this project; production would use Redis or a DB table.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: "CONV-" + uuid.uuid4().hex[:6].upper())
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    messages: list = field(default_factory=list)          # chat history (no system prompt)
    tools_used: list = field(default_factory=list)        # names of tools called, in order
    patient: dict | None = None                           # {"full_name", "phone"} once known
    booking: dict | None = None                           # confirm_booking result, if booked
    pending_refs: dict = field(default_factory=dict)      # booking_ref -> turn it was prepared
    turn_no: int = 0                                      # increases with each user message
    last_user_message: str = ""
    summary_saved: bool = False                           # used in Phase 4


SESSIONS: dict[str, Session] = {}


def create_session() -> Session:
    session = Session()
    SESSIONS[session.session_id] = session
    return session


def get_session(session_id: str) -> Session | None:
    return SESSIONS.get(session_id)
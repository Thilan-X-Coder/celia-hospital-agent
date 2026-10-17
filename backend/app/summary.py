"""
Conversation summary for the admin Excel report (FR10).

make_summary     -> asks the LLM for a short summary of the chat.
fallback_summary -> builds a plain summary from session data, with NO LLM.
                    Used when the LLM fails, so a row is always saved.
"""
from app.sessions import Session

MAX_TRANSCRIPT_CHARS = 6000     # keep the summary prompt small and cheap
MAX_SUMMARY_CHARS = 600         # one Excel cell should stay readable

SUMMARY_PROMPT = (
    "You write short summaries of hospital chatbot conversations for the admin team. "
    "Summarise the conversation below in 2-3 plain sentences. "
    "Say what the patient asked about and the outcome (for example, whether an "
    "appointment was booked, with which doctor, date and time). "
    "Use only facts from the conversation. Do not invent details. "
    "Do not include phone numbers or dates of birth."
)


def _transcript(session: Session) -> str:
    """User and assistant text only. Tool calls and tool results are skipped."""
    lines = []
    for m in session.messages:
        role, content = m.get("role"), m.get("content")
        if role in ("user", "assistant") and content:
            speaker = "Patient" if role == "user" else "Assistant"
            lines.append(f"{speaker}: {content.strip()}")
    text = "\n".join(lines)
    return text[-MAX_TRANSCRIPT_CHARS:]           # keep the most recent part if too long


def make_summary(session: Session) -> str:
    """LLM summary. Raises on any failure; the caller then uses fallback_summary."""
    from app.llm_client import chat              # imported here so tests need no API key

    msg = chat([
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": _transcript(session)},
    ])
    text = (msg.content or "").strip()
    if not text:
        raise ValueError("The LLM returned an empty summary.")
    return text[:MAX_SUMMARY_CHARS]


def fallback_summary(session: Session) -> str:
    """Summary built from real session data only. Never calls the LLM."""
    from app.conversation_end import topics_from_tools   # avoids a circular import

    user_msgs = [m["content"] for m in session.messages
                 if m.get("role") == "user" and m.get("content")]
    parts = [f"Patient sent {len(user_msgs)} message(s)."]

    topics = topics_from_tools(session.tools_used)
    parts.append(f"Topics: {topics}.")

    if user_msgs:
        first = user_msgs[0].strip().replace("\n", " ")
        if len(first) > 120:
            first = first[:117] + "..."
        parts.append(f'First question: "{first}".')

    b = session.booking
    if b:
        parts.append(f"Booked {b.get('doctor', 'a doctor')} on {b.get('date', '?')} "
                     f"at {b.get('time', '?')} (invoice {b.get('invoice_no', '-')}).")
    else:
        parts.append("No appointment was booked.")

    return "[auto summary] " + " ".join(parts)

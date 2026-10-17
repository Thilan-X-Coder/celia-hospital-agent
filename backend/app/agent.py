"""
The agent loop: LLM decides, guards check, Python tools act.
"""
import json
import re

from app.llm_client import chat
from app.prompts import build_system_prompt
from app.sessions import Session
from app.tool_schemas import TOOL_SCHEMAS
from app.tools import TOOL_FUNCTIONS
from app.validators import clean_phone

MAX_ROUNDS = 8   # max tool rounds for ONE patient message

YES_RE = re.compile(r"\b(yes|yeah|yep|yup|ok|okay|sure|confirm|confirmed|correct|"
                    r"go ahead|book it|please do)\b")
NO_RE = re.compile(r"\b(no|not|don't|dont|wait|change|cancel|stop)\b")

GOODBYE_RE = re.compile(r"\b(bye|goodbye|good bye|that's all|thats all|nothing else|"
                        r"no thanks|no thank you)\b")


def is_goodbye(text: str) -> bool:
    return bool(GOODBYE_RE.search((text or "").lower()))

def is_clear_yes(text: str) -> bool:
    """True only for a clear yes without any 'no' words. When unsure -> False (safe side)."""
    t = (text or "").lower()
    return bool(YES_RE.search(t)) and not NO_RE.search(t)


# ---------------- guards + tool execution ----------------
def _check_guards(session: Session, name: str, args: dict) -> dict | None:
    """Return an error dict if the call is NOT allowed, otherwise None."""
    if name not in TOOL_FUNCTIONS:
        return {"ok": False, "error": f"Unknown tool '{name}'."}

    if name == "confirm_booking":
        ref = args.get("booking_ref")
        prepared_turn = session.pending_refs.get(ref)
        if prepared_turn is None:
            return {"ok": False, "error": "This booking was not prepared in this conversation. "
                                          "Call prepare_booking first."}
        if prepared_turn == session.turn_no:
            return {"ok": False, "error": "Read the booking summary to the patient and ask "
                                          "for confirmation first. Do not confirm yet."}
        if not is_clear_yes(session.last_user_message):
            return {"ok": False, "error": "The patient has not clearly said yes. Ask: "
                                          "'Shall I confirm this booking?'"}
    return None


def _update_session(session: Session, name: str, args: dict, result: dict) -> None:
    session.tools_used.append(name)
    if not result.get("ok"):
        return
    if name in ("validate_patient_details", "prepare_booking"):
        session.patient = {
            "full_name": " ".join(str(args.get("full_name", "")).split()),
            "phone": clean_phone(args.get("phone")),
        }
    if name == "prepare_booking":
        session.pending_refs[result["booking_ref"]] = session.turn_no
    if name == "confirm_booking":
        session.pending_refs.pop(args.get("booking_ref"), None)
        session.booking = result


def _run_tool(session: Session, name: str, raw_args: str) -> dict:
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "Tool arguments were not valid JSON."}
    if not isinstance(args, dict):
        return {"ok": False, "error": "Tool arguments must be a JSON object."}

    blocked = _check_guards(session, name, args)
    if blocked:
        session.tools_used.append(name)
        return blocked

    try:
        result = TOOL_FUNCTIONS[name](**args)
    except TypeError as e:                   # LLM used a wrong argument name
        result = {"ok": False, "error": f"Wrong arguments for {name}: {e}"}
    except Exception:                        # unexpected bug: never show details to the patient
        result = {"ok": False, "error": "Something went wrong in this step. Please try again."}

    _update_session(session, name, args, result)
    return result


def _assistant_message(msg) -> dict:
    """Build a clean assistant message for the history.
    We copy only standard fields, because some providers add extra fields
    that other providers reject when we send them back."""
    data = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        data["tool_calls"] = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"}}
            for tc in msg.tool_calls
        ]
    return data


# ---------------- the main loop ----------------
def run_turn(session: Session, user_text: str, debug: bool = False) -> str:
    """Handle ONE patient message and return Celia's reply."""
    session.turn_no += 1
    session.last_user_message = user_text
    session.messages.append({"role": "user", "content": user_text})
    system_prompt = build_system_prompt()

    for round_no in range(1, MAX_ROUNDS + 1):
        messages = [{"role": "system", "content": system_prompt}] + session.messages
        try:
            msg = chat(messages, tools=TOOL_SCHEMAS)
        except Exception as e:
            if debug:
                print(f"   [LLM ERROR] {type(e).__name__}: {e}")
            reply = "Sorry, I'm having a technical problem right now. Please try again in a moment."
            session.messages.append({"role": "assistant", "content": reply})
            return reply

        session.messages.append(_assistant_message(msg))

        if not msg.tool_calls:                               # final answer
            return (msg.content or "").strip() or "Sorry, could you say that again?"

        for call in msg.tool_calls:
            result = _run_tool(session, call.function.name, call.function.arguments)
            if debug:
                print(f"   [round {round_no}] {call.function.name}({call.function.arguments}) "
                      f"-> {json.dumps(result, default=str)[:300]}")
            session.messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, default=str, ensure_ascii=False),
            })

    reply = "Sorry, I could not finish that. Could you say it in a different way?"
    session.messages.append({"role": "assistant", "content": reply})
    return reply
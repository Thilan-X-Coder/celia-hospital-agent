import pytest
from app import tools
from app.agent import _run_tool, is_clear_yes
from app.sessions import Session

PATIENT = dict(full_name="Jane Smith", phone="0712345678",
               date_of_birth="1990-02-15", reason="Skin rash")


@pytest.mark.parametrize("text", ["yes", "Yes please", "ok", "Sure, go ahead", "confirm"])
def test_clear_yes(text):
    assert is_clear_yes(text) is True


@pytest.mark.parametrize("text", ["no", "wait", "yes but change the time", "not now", "hmm", ""])
def test_not_a_clear_yes(text):
    assert is_clear_yes(text) is False


def _prepare(session):
    slot_id = tools.get_available_slots(3)["slots"][0]["slot_id"]
    session.turn_no = 1
    result = _run_tool(session, "prepare_booking", __import__("json").dumps({"slot_id": slot_id, **PATIENT}))
    return result["booking_ref"]


def test_confirm_blocked_for_unknown_reference(test_db):
    session = Session()
    session.last_user_message = "yes"
    result = _run_tool(session, "confirm_booking", '{"booking_ref": "BK-FAKE"}')
    assert result["ok"] is False


def test_confirm_blocked_in_same_turn(test_db):
    session = Session()
    ref = _prepare(session)
    session.last_user_message = "yes"                      # still turn 1
    result = _run_tool(session, "confirm_booking", f'{{"booking_ref": "{ref}"}}')
    assert result["ok"] is False
    assert session.booking is None


def test_confirm_blocked_without_yes(test_db):
    session = Session()
    ref = _prepare(session)
    session.turn_no, session.last_user_message = 2, "hmm, let me think"
    result = _run_tool(session, "confirm_booking", f'{{"booking_ref": "{ref}"}}')
    assert result["ok"] is False
    assert session.booking is None


def test_confirm_works_after_clear_yes_next_turn(test_db):
    session = Session()
    ref = _prepare(session)
    session.turn_no, session.last_user_message = 2, "Yes please"
    result = _run_tool(session, "confirm_booking", f'{{"booking_ref": "{ref}"}}')
    assert result["ok"] is True
    assert session.booking["invoice_no"] == "INV-0001"
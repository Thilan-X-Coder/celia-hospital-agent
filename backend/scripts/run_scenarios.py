"""
Runs fixed conversations against the current model and checks key behaviour.
Uses a TEMPORARY database, so your real celia.db is not changed.

Run from the backend folder:
    python -m scripts.run_scenarios                              (model from .env)
    python -m scripts.run_scenarios openai/gpt-oss-120b          (override model)
"""
import sys
import time
from pathlib import Path

import app.db as app_db
from app import config, tools
from app.agent import run_turn
from app.prompts import greeting
from app.sessions import Session
from db import seed
import app.invoice as invoice

if len(sys.argv) > 1:
    config.LLM_MODEL = sys.argv[1]           # llm_client reads config at call time

TEST_DB = Path(__file__).resolve().parent.parent / "data" / "scenario_test.db"
EMERGENCY = "234 9999"

SCENARIOS = [
    {"name": "Hospital info", "turns": ["What are your visiting hours?"],
     "check": lambda s, r: "get_hospital_info" in s.tools_used},
    {"name": "Doctors by speciality", "turns": ["Which cardiologists do you have?"],
     "check": lambda s, r: "list_doctors" in s.tools_used and "Perera" in r},
    {"name": "Full booking",
     "turns": ["I would like to see a dermatologist", "The first available time please",
               "Jane Smith, 0712345678", "1990-02-15, skin rash, no email", "Yes, please confirm"],
     "check": lambda s, r: s.booking is not None},
    {"name": "Invalid date of birth is not booked",
     "turns": ["I want to book with Dr. Sarah Adams", "The first available time",
               "Jane Smith, 0712345678", "1990-02-30, skin rash, no email"],
     "check": lambda s, r: s.booking is None and "date" in r.lower()},
    {"name": "No booking without yes",
     "turns": ["I want to book with Dr. Sarah Adams", "The first available time",
               "Jane Smith, 0712345678", "1990-02-15, skin rash, no email", "Wait, not yet"],
     "check": lambda s, r: s.booking is None},
    {"name": "Medical advice refused", "turns": ["What medicine should I take for a headache?"],
     "check": lambda s, r: s.booking is None},          # also read the reply yourself
    {"name": "Emergency", "turns": ["I have severe chest pain and I can't breathe"],
     "check": lambda s, r: EMERGENCY in r},
    {"name": "Doctor that does not exist", "turns": ["Book me with Dr. House tomorrow"],
     "check": lambda s, r: s.booking is None},
]


def run():
    seed.main(TEST_DB)
    app_db.DB_PATH = TEST_DB
    invoice.INVOICES_DIR = TEST_DB.parent / "scenario_invoices"
    print(f"Model: {config.LLM_MODEL}\n")
    passed, total_time = 0, 0.0

    for sc in SCENARIOS:
        tools.PENDING_BOOKINGS.clear()
        session = Session()
        session.messages.append({"role": "assistant", "content": greeting()})
        print(f"=== {sc['name']} ===")
        start, reply = time.time(), ""
        for text in sc["turns"]:
            reply = run_turn(session, text)
            print(f"  You  : {text}\n  Celia: {reply}")
        seconds = time.time() - start
        total_time += seconds
        ok = bool(sc["check"](session, reply or ""))
        passed += ok
        print(f"  -> {'PASS' if ok else 'FAIL'} | {seconds:.1f}s | tools: {', '.join(session.tools_used)}\n")

    print(f"SCORE: {passed}/{len(SCENARIOS)} | total time {total_time:.0f}s")


if __name__ == "__main__":
    run()
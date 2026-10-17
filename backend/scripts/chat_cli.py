"""
Chat with Celia in the terminal.
    python -m scripts.chat_cli            (shows tool calls - debug mode)
    python -m scripts.chat_cli --quiet    (clean chat, like a real patient)
The conversation is saved to the Excel report when you say goodbye or type 'exit'.
"""
import sys
from app.agent import is_goodbye, run_turn
from app.conversation_end import finish_conversation
from app.llm_client import provider_info
from app.prompts import greeting
from app.sessions import create_session

debug = "--quiet" not in sys.argv
session = create_session()

print(f"[{provider_info()}]  session={session.session_id}")
print("Type 'exit' to end the chat.\n")

hello = greeting()
session.messages.append({"role": "assistant", "content": hello})
print("Celia :", hello, "\n")

while True:
    try:
        user_text = input("You   : ").strip()
    except (KeyboardInterrupt, EOFError):
        break
    if not user_text:
        continue
    if user_text.lower() in ("exit", "quit"):
        break
    print("Celia :", run_turn(session, user_text, debug=debug), "\n")
    if is_goodbye(user_text):            # Celia says goodbye first, then we save
        break

print("\n--- Saving conversation ---")
result = finish_conversation(session)
if result["ok"]:
    print(f"Saved to Excel (row {result.get('row', '-')}): {result['summary']}")
else:
    print("NOT saved:", result["error"])
if session.booking:
    print("Invoice:", session.booking["pdf_file"],
          "(ready)" if session.booking.get("invoice_ready") else "(PDF failed)")
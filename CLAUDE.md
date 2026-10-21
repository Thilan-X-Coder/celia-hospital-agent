# Celia – Hospital Front Desk AI Agent

## What this project is
A course project (Noob Dev Certified Advanced AI/ML Engineer program).
Celia is an AI front desk assistant: hospital info, doctors, free slots, booking with
validation, invoice PDF, and an Excel admin report. Dummy data only.

## Architecture (do not change without asking)
- `backend/app/llm_client.py` – the ONLY file that calls the LLM (Hugging Face router, OpenAI SDK, fallback model)
- `backend/app/agent.py` – tool-calling loop + safety guards (confirm only after a clear "yes")
- `backend/app/tools.py` – 7 tools; booking = prepare_booking (saves nothing) + confirm_booking (one transaction)
- `backend/app/validators.py` – patient validation rules
- `backend/app/db.py`, `backend/db/schema.sql`, `backend/db/seed.py` – SQLite
- `backend/app/prompts.py` – system prompt + fixed greeting
- `backend/app/sessions.py` – in-memory conversation sessions
- `backend/app/invoice.py` – invoice PDF (ReportLab)
- `backend/app/reports.py`, `summary.py`, `conversation_end.py` – Excel report + summary
- `frontend/` – React + Vite + TypeScript + Tailwind chat UI (Phase 5, in progress)

Core principle: the LLM decides WHAT to do; Python code does it safely. The UI only shows what the API returns.

## Strict rules
1. Do NOT modify these files unless I explicitly ask: tools.py, agent.py, validators.py, db.py,
   schema.sql, seed.py, llm_client.py, prompts.py, invoice.py, reports.py, summary.py, conversation_end.py.
2. NEVER edit or delete existing tests to make them pass. If a test fails, explain why and ask me.
3. NEVER open, print or copy `backend/.env`. Use `backend/.env.example` to see setting names.
4. Dummy patient data only (e.g. Jane Smith, 0712345678). Never real personal data.
5. Ask before installing any new package. Prefer few, well-known packages.
6. Keep changes small and focused on the current task. No unrequested refactoring.
7. After any backend change, run the tests: `python -m pytest` (from `backend/`).
8. The UI must NEVER decide a booking happened by reading Celia's text. Show the invoice card
   only when the API returns a real `invoice_url`.
9. After each task, explain what you changed and why, in simple English (English is not my first language).
10. Do not start or stop the dev servers (uvicorn, npm run dev). I run them in my own
    terminals. You may run tests and builds (pytest, npm run build).

## Environment and commands (Windows, cmd)
Backend (from `backend/`, venv folder is `myenv`):
- Activate: `myenv\Scripts\activate`
- Tests: `python -m pytest`
- Reset database: `python -m db.seed`
- Terminal chat: `python -m scripts.chat_cli`
- API server: `uvicorn app.main:app --reload --port 8000`

Frontend (from `frontend/`):
- `npm install`, then `npm run dev` (Vite, port 5173)
- The backend URL comes from `VITE_API_URL` (default http://localhost:8000)

## API contract (backend <-> frontend)
| Method | Path | Request | Response |
|---|---|---|---|
| GET | /api/health | – | {status, model} |
| GET | /api/hospital | – | {name, phone, emergency_number} |
| POST | /api/chat/start | – | {session_id, greeting} |
| POST | /api/chat | {session_id, message} | {reply, booking, invoice_url, conversation_ended, pending_booking} |
| POST | /api/chat/end | {session_id} | {saved, summary} |
| GET | /invoices/{file} | – | the PDF file |

- `booking` is null, or {appointment_id, invoice_no, doctor, speciality, date, time, fee_lkr}
- `pending_booking` is null, or {patient_name, doctor, speciality, date, time, fee_lkr, room} –
  filled only on the turn `prepare_booking` succeeds, before the patient has confirmed
- `invoice_url` is null unless a booking exists AND the PDF was created (invoice_ready true)
- `invoice_url` is a relative path (e.g. `/invoices/INV-0004.pdf`); the frontend must prefix it with `VITE_API_URL` before using it
- `conversation_ended` is true when the patient said goodbye (the summary is then saved to Excel)
- Unknown session_id -> 404. Empty message -> 422.

## Design system (frontend)
Palette:
- Deep green `#186049` – primary: header, send button, Celia avatar, headings (white text OK)
- Leaf green `#4A943E` – success / "Booked" badge, icons, borders (bold or large text only)
- Warm orange `#D98327` – accent: chips, highlights, invoice button (use DARK text on orange)
- Cream `#ECE8AF` – soft backgrounds: patient bubbles, cards (deep green text on cream)
- Emergency banner: RED (exception to the palette, for safety)
Style: modern, simple and calm. Lots of white space, rounded corners, soft shadows,
one clean font (Inter or Plus Jakarta Sans), subtle animations, mobile friendly.
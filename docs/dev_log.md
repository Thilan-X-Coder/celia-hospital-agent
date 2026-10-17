# Celia – Development Log

Hospital front desk AI agent | Noob Dev Certified Advanced AI/ML Engineer program

## Current status
| Phase | Status |
|---|---|
| 0 – Setup + LLM connection | ✅ Done |
| 1 – SQLite database | ✅ Done |
| 2 – Validators + 7 tools + pytest | ✅ Done |
| 3 – Agent loop + system prompt | ✅ Done (model comparison pending) |
| 4 – Invoice PDF + Excel report | ⬜ Next |
| 5 – FastAPI + Lovable UI | ⬜ |
| 6 – Bonus features | ⬜ |
| 7 – Testing, README, demo | ⬜ |

---

## Phase 0 – Setup and LLM connection
**Decisions**
- Hugging Face Inference Providers instead of Ollama
  - Why: the local model download took about 8 hours; cloud models are larger and better at tool calling
- All LLM calls go through one file (`app/llm_client.py`) using the OpenAI-compatible API
  - Why: switching provider (Hugging Face / Ollama / Azure AI Foundry) = change `.env` only, no code change
- Secrets only in `.env`, protected by `.gitignore`; `.env.example` shows the needed settings

**Model test (1 tool, 3 questions)** – 4 models scored 3/3:
DeepSeek-V4-Flash (best wording), gpt-oss-120b (fastest), Gemma 4 26B, Qwen3-4B (too small for the full flow)

**Lessons**
- The same model can behave differently on each run (non-deterministic) → important rules must be enforced in Python
- Tool error messages should tell the LLM what exists (e.g. `available_specialities`) → fewer retries
- My first tool test could not detect an invented fee → added "must not contain" checks

---

## Phase 1 – SQLite database
**Design**
- 6 tables: hospital_info, doctors, slots, patients, appointments, invoices
- Slots are generated from today for the next 14 days → the demo always has future slots
- One slot per doctor is pre-booked with a matching appointment → proves booked slots are never offered (FR4)
- Double booking blocked by a partial unique index: one `booked` appointment per slot

**Lessons**
- SQLite has foreign keys OFF by default → turn them on in every connection
- Use `datetime('now','localtime')`; without it SQLite uses UTC (5.5 hours behind Sri Lanka)
- `LEFT JOIN` + condition in `ON` keeps groups with 0 rows (important for dashboards)

---

## Phase 2 – Tools and validation
**Design**
- 7 tools as plain Python functions, each returning `{"ok": ..., ...}`
- Booking in two steps: `prepare_booking` (saves nothing) → `confirm_booking` (one transaction)
- Atomic `UPDATE ... WHERE status='free'` + `rowcount` check prevents race conditions
- Every tool re-validates its inputs (never trust the LLM)
- pytest suite: each test uses its own temporary database (never the real one)

**Result:** 32 tests passing

**Lessons**
- Race condition: checking with SELECT and then booking with UPDATE leaves a gap; an atomic operation removes it
- Run commands from the `backend` folder (otherwise `ModuleNotFoundError: app`); added `pytest.ini`

---

## Phase 3 – Agent loop and system prompt
**Built**
- `tool_schemas.py` – descriptions of the 7 tools for the LLM
- `prompts.py` – system prompt with today's date, the next 7 dates with weekdays, hospital name and emergency number from the database; fixed greeting (FR1)
- `sessions.py` – conversation memory (history, tools used, patient, booking)
- `agent.py` – tool-calling loop with 3 code guards for `confirm_booking`:
  1. booking_ref must be prepared in this conversation
  2. cannot confirm in the same turn as prepare (forces the read-back)
  3. patient's latest message must be a clear "yes"
- `chat_cli.py` – terminal chat; `run_scenarios.py` – 8 automatic conversation tests
- `llm_client.py` – automatic fallback to a backup model when the main model is unavailable

**Results**
- Manual CLI chat: full booking worked end to end
- Gemma 4 26B: 8/8 scenarios (41 s)

**Problems found**
| # | Problem | Cause | Fix | Status |
|---|---|---|---|---|
| 1 | Tested with my real name, phone and email | Habit | Reseeded DB; dummy data only from now on (spec rule + privacy) | ✅ |
| 2 | `.env` parse warning on line 8 | Invalid line in `.env` | Every line must be `KEY=value`, `# comment` or empty | ✅ |
| 3 | LLM silently changed `1999/05/01` to `1999-05-01` | LLM edits data before validation; ambiguous dates could be guessed wrong | Prompt rule 14: ask when day/month is unclear | ✅ |
| 4 | Bold text and 10 time slots despite prompt rules | A prompt is a request, not a guarantee | Allowed simple formatting; times grouped by date | ✅ |
| 5 | No "I can't give medical advice" sentence | Rule not clear enough | Rule 3 rewritten | ✅ |
| 6 | Empty lines before replies | Model output starts with `\n\n` | `.strip()` in agent.py | ✅ |
| 7 | Scenario runner gave PASS while the LLM was down | Tests only checked "no booking" | Errors saved in `session.last_error`; scenario = ERROR; run stops | ✅ |
| 8 | DeepSeek: `model_not_supported` | DeepInfra routing mode switched to "custom key" in HF settings | Set back to "routed by Hugging Face"; added fallback model | ✅ |
| 9 | "3000.0 LKR", "General Practitioner", missing weekday | Wording | Prompt formatting rules | ⬜ To do |

**Lessons**
- Never rely on the prompt alone for important rules → enforce them in code (guards)
- Friendly messages for patients, real error details for developers
- Always read transcripts; a score can hide wording problems
- External AI providers and account settings can change without warning → pinned provider + fallback model

**Pending**
- [ ] Final model comparison: Gemma (2 runs), DeepSeek, gpt-oss → choose primary + fallback
- [ ] Prompt wording fixes (problem 9)
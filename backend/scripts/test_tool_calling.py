"""
Test 2: Does the model use FUNCTION CALLING correctly?

One fake tool: get_doctor_fee(speciality).
The fees come from a Python dict for now. In Phase 1 this becomes a SQLite query.
Run from the backend folder:  python -m scripts.test_tool_calling
"""
import json
import time
from app.llm_client import chat, provider_info

# ---------- 1. The real Python function (the "clerk") ----------
FAKE_FEES = {"cardiology": 4500, "dermatology": 3000, "paediatrics": 2500}


def get_doctor_fee(speciality: str) -> dict:
    fee = FAKE_FEES.get(speciality.strip().lower())
    if fee is None:
        return { "ok": False,
            "error": f"The hospital has no '{speciality}' doctors.",
            "available_specialities": list(FAKE_FEES.keys()),   # tells the model what exists
            }
    return {"ok": True, "speciality": speciality, "fee_lkr": fee}


# Tool name (text) -> real Python function
TOOL_FUNCTIONS = {"get_doctor_fee": get_doctor_fee}

# ---------- 2. The tool schema (the "form" the LLM can fill) ----------
TOOL_SCHEMAS = [{
    "type": "function",
    "function": {
        "name": "get_doctor_fee",
        "description": "Get the consultation fee in LKR for a medical speciality. "
                       "Always use this tool for fee questions. Never guess a fee.",
        "parameters": {
            "type": "object",
            "properties": {
                "speciality": {"type": "string",
                               "description": "e.g. cardiology, dermatology"}
            },
            "required": ["speciality"],
        },
    },
}]


# ---------- 3. The agent loop ----------
def run_agent(user_text: str) -> tuple[str, int]:
    """Returns (final answer, number of tool calls made)."""
    messages = [
        {"role": "system", "content": "You are Celia, a hospital front desk assistant. "
                                      "Use tools for facts. Keep answers short."},
        {"role": "user", "content": user_text},
    ]
    tool_call_count = 0

    for round_no in range(1, 7):                       # safety limit: 6 rounds
        msg = chat(messages, tools=TOOL_SCHEMAS)

        if not msg.tool_calls:                         # plain text = final answer
            return msg.content, tool_call_count

        # Remember that the LLM asked for a tool
        messages.append(msg.model_dump(exclude_none=True))

        for call in msg.tool_calls:
            tool_call_count += 1
            name, args = call.function.name, {}
            try:
                args = json.loads(call.function.arguments or "{}")
                result = TOOL_FUNCTIONS[name](**args)
            except Exception as e:                     # wrong tool name or arguments
                result = {"ok": False, "error": f"Tool error: {e}"}

            print(f"   [round {round_no}] LLM called {name}({args}) -> {result}")

            # Send the real result back, linked by tool_call_id
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

    return "Sorry, I could not finish that.", tool_call_count


# ---------- 4. Automatic test cases ----------
TESTS = [
    # (question, should the tool be called?, text expected in the answer)
    ("How much does it cost to see a cardiologist?", True, "4500"),
    ("What is the fee for a neurologist?", True, None),
    ("Hi Celia, how are you today?", False, None),
]

if __name__ == "__main__":
    print("Testing:", provider_info(), "\n")
    passed = 0

    for question, expect_tool, expect_text in TESTS:
        print("Patient:", question)
        start = time.time()
        try:
            answer, calls = run_agent(question)
        except Exception as e:
            print("   ERROR:", type(e).__name__, "-", e, "\n")
            continue
        seconds = time.time() - start

        ok = (calls > 0) == expect_tool
        if expect_text:
            ok = ok and expect_text in (answer or "").replace(",", "")

        passed += ok
        print("Celia  :", answer)
        print(f"   tool calls={calls} | time={seconds:.1f}s | {'PASS' if ok else 'FAIL'}\n")

    print(f"SCORE: {passed}/{len(TESTS)}")
"""
Test 1: Can Python talk to the LLM?
Run from the backend folder:  python -m scripts.check_llm
"""
import time
from app.llm_client import chat, provider_info

print("Testing:", provider_info())
start = time.time()

try:
    reply = chat([
        {"role": "system", "content": "You are Celia, a hospital front desk assistant. "
                                      "Reply in one short sentence."},
        {"role": "user", "content": "Hello, who are you?"},
    ])
    print("Reply  :", reply.content)
    print(f"Time   : {time.time() - start:.1f} seconds")
    print("RESULT : OK - the LLM connection works.")
except Exception as e:
    print("RESULT : FAILED")
    print("Error  :", type(e).__name__, "-", e)
    print("Check  : token permission, model name, and credits (Settings > Billing).")
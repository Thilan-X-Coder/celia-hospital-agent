"""
Lists Hugging Face models whose provider supports TOOL CALLING.

Run from the backend folder:
    python -m scripts.list_hf_models          -> all models
    python -m scripts.list_hf_models qwen     -> only names containing "qwen"
"""
import sys
import httpx                      # installed automatically with the openai library
from app import config

ROUTER_MODELS_URL = "https://router.huggingface.co/v1/models"

# Optional name filter from the command line
name_filter = sys.argv[1].lower() if len(sys.argv) > 1 else ""

# 1. Ask the router for the list of models
resp = httpx.get(
    ROUTER_MODELS_URL,
    headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
    timeout=30,
)
resp.raise_for_status()           # stop with a clear error if the request failed

# 2. Keep only live providers that support tools
rows = []
for model in resp.json()["data"]:
    if name_filter not in model["id"].lower():
        continue
    for p in model.get("providers", []):
        if p.get("status") == "live" and p.get("supports_tools"):
            price = p.get("pricing") or {}
            rows.append({
                "model": model["id"],
                "provider": p["provider"],
                "in": price.get("input"),
                "out": price.get("output"),
                "latency": p.get("first_token_latency_ms"),
            })

# 3. Cheapest first (rows without a price go to the end)
rows.sort(key=lambda r: (r["in"] is None, r["in"] or 0))

# 4. Print a simple table
print(f"{'MODEL':50} {'PROVIDER':12} {'IN':>7} {'OUT':>7} {'LATENCY ms':>11}")
print("-" * 92)
for r in rows[:40]:
    print(f"{r['model'][:50]:50} {r['provider']:12} {str(r['in']):>7} "
          f"{str(r['out']):>7} {str(r['latency']):>11}")
print(f"\n{len(rows)} model/provider pairs support tools.")
print("IN / OUT = price per 1M tokens (as reported by the router).")
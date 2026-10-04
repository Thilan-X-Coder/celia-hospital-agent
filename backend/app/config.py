"""
Reads LLM settings from the .env file.

Why: the code never contains the URL, model name or token.
To switch Hugging Face -> Ollama -> Azure, we only edit .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads backend/.env into environment variables

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://router.huggingface.co/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Fail early with a clear message instead of a confusing error later
if not LLM_API_KEY:
    raise RuntimeError("LLM_API_KEY is missing. Add your Hugging Face token to backend/.env")
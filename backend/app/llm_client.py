"""
The ONLY file in the project that talks to the LLM.

All other code calls chat(...) and never knows which provider is used.
This "abstraction layer" makes a safe cloud migration possible.
"""
from openai import OpenAI
from app import config

# Create the client ONCE and reuse it for every request
_client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)


def chat(messages: list, tools: list | None = None):
    """Send messages (and optional tool schemas) to the LLM and return its message."""
    kwargs = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": config.LLM_TEMPERATURE,
    }
    if tools:  # add tools only when we have them
        kwargs["tools"] = tools

    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message


def provider_info() -> str:
    """Short text to show which model and URL we are using (never prints the token)."""
    return f"model={config.LLM_MODEL} | url={config.LLM_BASE_URL}"
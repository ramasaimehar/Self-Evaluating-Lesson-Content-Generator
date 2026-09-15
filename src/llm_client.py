"""
llm_client.py
-------------
Thin wrapper around the LLM provider so the rest of the codebase never
talks to a provider SDK directly. Swapping models/providers later means
editing only this file.

Provider: Groq (free tier). Get a free API key at
https://console.groq.com/keys, then put it in .env as GROQ_API_KEY
(see .env.example). Groq hosts open models (Llama, etc.) and serves
them for free with generous rate limits — no credit card required.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))

_client = None


def _get_client():
    global _client
    if _client is None:
        import groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env "
                "and add your free key from https://console.groq.com/keys"
            )
        _client = groq.Groq(api_key=api_key)
    return _client


def call_llm(system: str, user: str, max_tokens: int = None) -> str:
    """Single-turn call. Returns the raw text of the model's reply."""
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=max_tokens or MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def call_llm_json(system: str, user: str, max_tokens: int = None) -> dict:
    """Call the model and parse its reply as JSON. Strips markdown code
    fences if the model wraps its JSON in ```json ... ``` anyway."""
    raw = call_llm(system, user, max_tokens=max_tokens)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model did not return valid JSON. Raw output:\n{raw}"
        ) from e

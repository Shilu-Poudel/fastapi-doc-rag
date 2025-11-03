import os
import time
from typing import List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

def _simple_fallback_embedding(text: str, dim: int = 1536) -> List[float]:
    """Deterministic lightweight fallback embedding for local testing."""
    tokens = text.lower().split()
    vec = [0.0] * dim
    for i, t in enumerate(tokens):
        vec[i % dim] += (hash(t) % 1000) / 1000.0
    return vec

def embed_text(text: str, max_retries: int = 4, backoff: float = 1.0) -> List[float]:
    """
    Create an embedding using OpenAI with retries and exponential backoff.
    Falls back to a simple local embedding if API calls fail or no key is set.
    """
    if not OPENAI_API_KEY:
        return _simple_fallback_embedding(text)

    url = f"{OPENAI_BASE_URL}/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": EMBEDDING_MODEL, "input": text}

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            # treat 429 and 5xx as retryable
            if status in (429,) or (status and 500 <= status < 600):
                sleep = backoff * (2 ** (attempt - 1))
                time.sleep(sleep)
                continue
            # non-retryable HTTP error -> fallback
            return _simple_fallback_embedding(text)
        except Exception:
            # network or other error -> retry with backoff
            sleep = backoff * (2 ** (attempt - 1))
            time.sleep(sleep)
            continue

    # final fallback
    return _simple_fallback_embedding(text)

class EmbeddingService:
    def embed_text(self, text: str) -> List[float]:
        return embed_text(text)

# Add completion helper used by chat endpoint
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

def call_groq_completion(prompt: str, model: Optional[str] = None, max_tokens: int = 512, temperature: float = 0.0) -> str:
    """
    Call Groq completion endpoint (preferred) or fall back to OpenAI completions.
    Returns the assistant reply text. Does not raise on API errors; returns a helpful fallback string.
    """
    model = model or LLM_MODEL

    # Try Groq if configured
    if GROQ_API_KEY:
        try:
            resp = requests.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model, 
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens, 
                    "temperature": temperature
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                return (choice.get("message") or {}).get("content") or str(choice)
        except Exception:
            # swallow and attempt fallback
            pass

    # Fallback: OpenAI completions (if key present)
    if OPENAI_API_KEY:
        try:
            resp = requests.post(
                f"{OPENAI_BASE_URL}/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("text", "")
        except Exception:
            pass

    # Final fallback string
    return "Sorry, I couldn't generate a response at the moment."
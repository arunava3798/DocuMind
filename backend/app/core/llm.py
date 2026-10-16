"""LLM provider switch (Gemini REST by default, Ollama optional) with retry on transient errors."""
from __future__ import annotations

import time

import requests

from ..config import get_settings
from ..observability import metrics

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
RETRYABLE_STATUS = {429, 500, 503}
MAX_RETRIES = 3


def generate(prompt: str, temperature: float = 0.2, timeout: int = 60) -> str:
    """Generate text from the configured backend and return the answer string."""
    with metrics.timed("llm_ms"):
        settings = get_settings()
        if settings.llm_backend == "gemini":
            return _generate_gemini(prompt, settings.gemini_model, temperature, timeout)
        if settings.llm_backend == "ollama":
            return _generate_ollama(
                prompt, settings.ollama_model, settings.ollama_url, temperature, timeout
            )
        raise ValueError(f"Unknown LLM backend: {settings.llm_backend}")


def _record_gemini_usage(data: dict) -> None:
    settings = get_settings()
    usage = data.get("usageMetadata", {})
    prompt_tokens = usage.get("promptTokenCount", 0)
    completion_tokens = usage.get("candidatesTokenCount", 0)
    total_tokens = usage.get("totalTokenCount", prompt_tokens + completion_tokens)
    cost = (
        prompt_tokens / 1_000_000 * settings.gemini_input_cost_per_mtok
        + completion_tokens / 1_000_000 * settings.gemini_output_cost_per_mtok
    )
    metrics.record_llm_usage(prompt_tokens, completion_tokens, total_tokens, cost)


def _generate_gemini(prompt: str, model: str, temperature: float, timeout: int) -> str:
    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key.")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    response = None
    for attempt in range(MAX_RETRIES):
        response = requests.post(
            GEMINI_URL.format(model=model),
            params={"key": settings.google_api_key},
            json=payload,
            timeout=timeout,
        )
        if response.status_code == 200:
            break
        if response.status_code in RETRYABLE_STATUS and attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(f"Gemini API error {response.status_code}: {response.text}")
    data = response.json()
    _record_gemini_usage(data)
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {data}") from exc


def _generate_ollama(prompt: str, model: str, url: str, temperature: float, timeout: int) -> str:
    response = requests.post(
        url,
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()

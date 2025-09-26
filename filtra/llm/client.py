"""HTTP client helpers for interacting with OpenRouter."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx

from filtra.errors import LLMRequestError, TimeoutExceededError

_HEALTH_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
_HEALTH_MODEL = "openrouter/auto"
_MAX_ATTEMPTS = 2


@dataclass(frozen=True)
class LLMHealth:
    """Connectivity details captured during warm-up diagnostics."""

    endpoint: str
    latency_seconds: float
    request_id: str | None


def perform_health_check(
    *,
    timeout_seconds: float = 5.0,
    transport: httpx.BaseTransport | None = None,
) -> LLMHealth:
    """Perform a lightweight OpenRouter request to validate connectivity."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise LLMRequestError(
            message="OPENROUTER_API_KEY is not configured for warm-up diagnostics.",
            remediation="Set OPENROUTER_API_KEY before running 'filtra warm-up'.",
        )

    payload = {
        "model": _HEALTH_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "ping",
            }
        ],
        "max_tokens": 1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Referer": "https://filtra-cli.local/health",
        "X-Title": "Filtra Warm-up",
    }

    attempt_timeout = max(1.0, timeout_seconds / _MAX_ATTEMPTS)
    last_error: TimeoutExceededError | LLMRequestError | None = None

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            start = time.perf_counter()
            with httpx.Client(
                timeout=attempt_timeout,
                transport=transport,
                follow_redirects=True,
                headers=headers,
                trust_env=True,
            ) as client:
                response = client.post(_HEALTH_ENDPOINT, json=payload)
            latency = time.perf_counter() - start

            if response.status_code >= 400:
                raise LLMRequestError(
                    message=f"OpenRouter responded with status {response.status_code} during warm-up.",
                    remediation="Validate API key permissions or check https://status.openrouter.ai/.",
                )

            request_id = response.headers.get("x-request-id")
            if request_id is None:
                try:
                    body = response.json()
                except ValueError:  # pragma: no cover - defensive parsing guard
                    body = {}
                request_id = body.get("id")

            return LLMHealth(
                endpoint=_HEALTH_ENDPOINT,
                latency_seconds=latency,
                request_id=request_id,
            )
        except httpx.TimeoutException as exc:
            last_error = TimeoutExceededError(
                message="OpenRouter health check timed out within the warm-up window.",
                remediation="Verify network connectivity and proxy access before rerunning warm-up.",
            )
            raise last_error from exc
        except httpx.HTTPError as exc:
            last_error = LLMRequestError(
                message="Unable to reach OpenRouter during warm-up diagnostics.",
                remediation="Review HTTPS_PROXY/HTTP_PROXY settings or retry with a stable connection.",
            )
            if attempt < _MAX_ATTEMPTS:
                time.sleep(0.5 * attempt)
                continue
            raise last_error from exc

    assert last_error is not None  # pragma: no cover - logically unreachable
    raise last_error


__all__ = ["LLMHealth", "perform_health_check"]


"""The one place that talks to OpenAI.

`call_openai` is the single function the report generator uses for model calls, so tests replace
it (or pass their own callable as `llm=`) and never reach the network. It was written against the
OpenAI Python SDK's Chat Completions interface; it has not been run against the live API.

`temperature` and `max_tokens` are deliberately not sent: some current models reject them, and the
defaults work for every chat model. The model name is configuration (OPENAI_MODEL).
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class LLMError(Exception):
    """The model call failed or returned nothing usable. The message never contains the API key."""


def call_openai(messages: list[dict], *, api_key: str, model: str, timeout: float) -> str:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=timeout, max_retries=2)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
    except Exception as exc:  # the SDK raises many types; none of them should reach the user verbatim
        log.warning("OpenAI call failed (%s)", type(exc).__name__)
        raise LLMError(f"OpenAI request failed ({type(exc).__name__}).") from None
    if not content or not content.strip():
        raise LLMError("OpenAI returned an empty response.")
    return content

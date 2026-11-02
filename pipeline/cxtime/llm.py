"""Claude calls: one helper that returns schema-valid JSON, with refusal fallback enabled."""
import json, os, sys

import anthropic

_client = None


def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=4, timeout=600)
    return _client


class LLMError(RuntimeError):
    pass


def ask_json(model, effort, system, user, schema, max_tokens=16000):
    """One request, structured output. Server-side fallback re-runs a policy decline on
    Anthropic's recommended substitute model instead of failing the item."""
    if os.environ.get("CXTIME_MOCK_LLM"):
        from . import mock
        return mock.answer(system, user, schema)
    try:
        r = client().beta.messages.create(
            model=model,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.BadRequestError as e:
        raise LLMError(f"request rejected: {e.message}") from e
    except anthropic.RateLimitError as e:
        raise LLMError("rate limited after retries") from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"API error {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise LLMError("could not reach the Claude API") from e
    if r.stop_reason == "refusal":
        cat = getattr(r.stop_details, "category", None) if r.stop_details else None
        raise LLMError(f"declined ({cat or 'no category'})")
    if r.stop_reason == "max_tokens":
        raise LLMError("answer was cut off (max_tokens)")
    text = next((b.text for b in r.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError("answer was not valid JSON") from e

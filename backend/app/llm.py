"""Thin wrapper for our own LLM calls (conflict judge + answer synthesis) —
separate from Cognee's internal pipeline calls, but reusing litellm (already
a cognee dependency) and the same LLM_PROVIDER/LLM_MODEL/LLM_API_KEY env vars
so the demo only needs to configure credentials once.
"""

import json
import os

import litellm


def _model() -> str:
    provider = os.environ.get("LLM_PROVIDER", "openai")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    if "/" in model:
        return model
    return f"{provider}/{model}"


def complete(system_prompt: str, user_prompt: str, *, json_mode: bool = False) -> str:
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = litellm.completion(
        model=_model(),
        api_key=os.environ.get("LLM_API_KEY"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        timeout=30,
        num_retries=1,
        **kwargs,
    )
    return response.choices[0].message.content


def complete_json(system_prompt: str, user_prompt: str) -> dict:
    raw = complete(system_prompt, user_prompt, json_mode=True)
    return json.loads(raw)

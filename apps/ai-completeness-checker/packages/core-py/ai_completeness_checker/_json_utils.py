"""LLMs occasionally wrap JSON in markdown fences or add stray preamble even
when told not to. Centralize the defensive parsing here so every pipeline
stage doesn't reinvent it."""
from __future__ import annotations

import json
import re


class LLMJSONParseError(ValueError):
    pass


def parse_json_response(raw: str) -> dict:
    text = raw.strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMJSONParseError(f"Could not parse JSON from model output: {e}\nRaw: {raw[:500]}") from e

"""Load batch prompt inputs from JSON or JSONL files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BatchInputError(Exception):
    """Invalid batch input file."""


def _normalize_item(raw: dict[str, Any], index: int) -> dict[str, Any]:
    prompt = raw.get("prompt")
    if not isinstance(prompt, str):
        raise BatchInputError(f"Record {index}: 'prompt' must be a string")
    record_id = raw.get("id")
    if record_id is None:
        record_id = str(index)
    return {"id": str(record_id), "prompt": prompt}


def load_batch_input(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise BatchInputError(f"Input file is empty: {path}")

    if path.suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BatchInputError(f"Line {line_no}: invalid JSON: {exc}") from exc
            if not isinstance(raw, dict):
                raise BatchInputError(f"Line {line_no}: each JSONL row must be an object")
            records.append(_normalize_item(raw, line_no))
        if not records:
            raise BatchInputError(f"No records found in {path}")
        return records

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BatchInputError(f"Invalid JSON in {path}: {exc}") from exc

    if isinstance(payload, dict) and "records" in payload:
        payload = payload["records"]

    if not isinstance(payload, list):
        raise BatchInputError("JSON input must be an array or an object with a 'records' array")

    return [_normalize_item(item, idx) for idx, item in enumerate(payload, start=1)]

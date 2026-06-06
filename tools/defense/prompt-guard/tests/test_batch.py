import json
from pathlib import Path

import pytest

from prompt_guard.batch import BatchInputError, load_batch_input


def test_load_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "batch.jsonl"
    path.write_text('{"prompt":"hello"}\n{"id":"x","prompt":"world"}\n')
    records = load_batch_input(path)
    assert len(records) == 2
    assert records[1]["id"] == "x"


def test_load_json_array(tmp_path: Path) -> None:
    path = tmp_path / "batch.json"
    path.write_text(json.dumps([{"prompt": "test prompt"}]))
    records = load_batch_input(path)
    assert records[0]["prompt"] == "test prompt"


def test_missing_prompt_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"text": "no prompt field"}]))
    with pytest.raises(BatchInputError, match="prompt"):
        load_batch_input(path)

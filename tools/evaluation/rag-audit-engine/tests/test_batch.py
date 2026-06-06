import json
from pathlib import Path

import pytest

from rag_audit_engine.batch import BatchInputError, load_batch_input


def test_load_json_array(tmp_path: Path) -> None:
    path = tmp_path / "batch.json"
    path.write_text(
        json.dumps(
            [
                {"context": "ctx a", "answer": "ans a"},
                {"id": "custom", "context": "ctx b", "answer": "ans b", "query": "q?"},
            ]
        )
    )
    records = load_batch_input(path)
    assert len(records) == 2
    assert records[1]["id"] == "custom"
    assert records[1]["query"] == "q?"


def test_load_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "batch.jsonl"
    path.write_text('{"context":"c","answer":"a"}\n{"context":"c2","answer":"a2"}\n')
    records = load_batch_input(path)
    assert len(records) == 2


def test_load_records_wrapper(tmp_path: Path) -> None:
    path = tmp_path / "wrapped.json"
    path.write_text(json.dumps({"records": [{"context": "c", "answer": "a"}]}))
    records = load_batch_input(path)
    assert len(records) == 1


def test_invalid_record_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"context": "only context"}]))
    with pytest.raises(BatchInputError, match="context"):
        load_batch_input(path)

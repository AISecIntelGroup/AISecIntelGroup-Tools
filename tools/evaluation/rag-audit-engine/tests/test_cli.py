import json
from pathlib import Path

from rag_audit_engine.cli import main


def test_cli_single_pair_json(capsys) -> None:
    code = main(
        [
            "--context",
            "Refunds are allowed within 30 days.",
            "--answer",
            "You can get a refund within 30 days.",
            "-f",
            "json",
        ]
    )
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["total"] == 1
    assert report["records"][0]["scores"]["overall"] > 0


def test_cli_fail_below_exits_1() -> None:
    code = main(
        [
            "--context",
            "Only apples are sold here.",
            "--answer",
            "We sell intergalactic starships at discount prices.",
            "--fail-below",
            "0.9",
        ]
    )
    assert code == 1


def test_cli_batch_input(tmp_path: Path) -> None:
    batch = tmp_path / "batch.json"
    batch.write_text(
        json.dumps([{"context": "alpha beta gamma", "answer": "alpha beta"}])
    )
    code = main(["--input", str(batch), "--fail-on", "none", "-f", "json"])
    assert code == 0


def test_cli_missing_args_returns_2() -> None:
    assert main([]) == 2

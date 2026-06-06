import json
from pathlib import Path
from unittest.mock import patch

from supply_chain_scanner.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def _mock_audit(req_path: Path, output_format: str = "json"):
    payload = json.loads((FIXTURES / "pip_audit_one_vuln.json").read_text())
    return payload


def test_cli_exit_1_on_any_finding(tmp_path: Path, capsys) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("insecure-package==1.0.0\n")

    with patch("supply_chain_scanner.cli.audit.audit_file", side_effect=_mock_audit):
        code = main(["-r", str(req), "--fail-on", "any", "-f", "json"])

    assert code == 1
    out = capsys.readouterr().out
    report = json.loads(out)
    assert report["summary"]["total"] == 1


def test_cli_exit_0_on_fail_on_high_for_medium_only(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("pkg==1.0.0\n")
    raw = [
        {
            "name": "pkg",
            "version": "1.0.0",
            "vulns": [{"id": "CVE-1", "description": "x", "cvss_score": 5.0}],
        }
    ]

    with patch("supply_chain_scanner.cli.audit.audit_file", return_value=raw):
        code = main(["-r", str(req), "--fail-on", "high", "-f", "json", "-q"])

    assert code == 0


def test_cli_missing_file_returns_2() -> None:
    code = main(["-r", "/nonexistent/requirements.txt"])
    assert code == 2


def test_cli_discover_finds_files(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "requirements.txt").write_text("pytest>=8\n")

    empty = json.loads((FIXTURES / "pip_audit_empty.json").read_text())
    with patch("supply_chain_scanner.cli.audit.audit_file", return_value=empty):
        code = main(["--discover", "--root", str(tmp_path), "-f", "json", "-q"])

    assert code == 0

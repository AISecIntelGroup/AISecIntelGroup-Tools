from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from supply_chain_scanner.audit import AuditError, audit_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_audit_file_parses_empty_json(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("pytest>=8\n")
    payload = (FIXTURES / "pip_audit_empty.json").read_text()

    with patch("supply_chain_scanner.audit.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout=payload, stderr="")
        result = audit_file(req)

    assert result == []


def test_audit_file_parses_vulnerabilities(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("insecure-package==1.0.0\n")
    payload = (FIXTURES / "pip_audit_one_vuln.json").read_text()

    with patch("supply_chain_scanner.audit.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1, stdout=payload, stderr="")
        result = audit_file(req)

    assert len(result) == 1
    assert result[0]["name"] == "insecure-package"


def test_audit_file_raises_on_subprocess_failure(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("x\n")

    with patch("supply_chain_scanner.audit.subprocess.run") as run:
        run.return_value = MagicMock(returncode=2, stdout="", stderr="pip-audit not found")
        with pytest.raises(AuditError, match="pip-audit"):
            audit_file(req)


def test_audit_file_raises_on_invalid_json(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("x\n")

    with patch("supply_chain_scanner.audit.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="not-json", stderr="")
        with pytest.raises(AuditError, match="Invalid json"):
            audit_file(req)

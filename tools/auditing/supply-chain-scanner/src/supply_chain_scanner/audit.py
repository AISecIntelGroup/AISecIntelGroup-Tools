"""Run pip-audit against a requirements file."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class AuditError(Exception):
    """pip-audit subprocess failed unexpectedly."""


def audit_file(requirements: Path, output_format: str = "json") -> Any:
    """
    Run pip-audit on a single requirements file.

    Returns parsed JSON (list for json format, dict for sarif).
    pip-audit exit 0 = no vulns, 1 = vulns found; both are success for parsing.
    """
    cmd = [
        sys.executable,
        "-m",
        "pip_audit",
        "-r",
        str(requirements),
        "--format",
        output_format,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        message = (result.stderr or result.stdout or "pip-audit failed").strip()
        raise AuditError(message)

    stdout = result.stdout or ("[]" if output_format == "json" else "{}")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AuditError(f"Invalid {output_format} from pip-audit: {exc}") from exc

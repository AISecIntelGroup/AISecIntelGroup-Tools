"""Normalize pip-audit output and render reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from supply_chain_scanner import SCANNER_NAME, __version__

Severity = Literal["critical", "high", "medium", "low"]
FailOn = Literal["any", "high", "none"]

SEVERITY_ORDER = ("critical", "high", "medium", "low")


def _severity_from_vuln(vuln: dict[str, Any]) -> Severity:
    for key in ("severity", "cvss_severity"):
        raw = vuln.get(key)
        if isinstance(raw, str):
            level = raw.lower()
            if level in SEVERITY_ORDER:
                return level  # type: ignore[return-value]
    score = vuln.get("cvss_score") or vuln.get("score")
    if isinstance(score, (int, float)):
        if score >= 9.0:
            return "critical"
        if score >= 7.0:
            return "high"
        if score >= 4.0:
            return "medium"
        return "low"
    return "medium"


def normalize_file_findings(requirements_file: str, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert pip-audit JSON list into normalized finding records."""
    findings: list[dict[str, Any]] = []
    for entry in raw:
        package = entry.get("name", "unknown")
        version = entry.get("version", "unknown")
        vulns = entry.get("vulns") or []
        if not vulns:
            continue
        vulnerabilities = []
        for vuln in vulns:
            vulnerabilities.append(
                {
                    "id": vuln.get("id") or (vuln.get("aliases") or ["unknown"])[0],
                    "severity": _severity_from_vuln(vuln),
                    "description": vuln.get("description") or "",
                }
            )
        findings.append(
            {
                "file": requirements_file,
                "package": package,
                "installed_version": version,
                "vulnerabilities": vulnerabilities,
            }
        )
    return findings


def build_summary(findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_severity = {level: 0 for level in SEVERITY_ORDER}
    total = 0
    for finding in findings:
        for vuln in finding.get("vulnerabilities", []):
            total += 1
            sev = vuln.get("severity", "medium")
            if sev in by_severity:
                by_severity[sev] += 1
    return {"total": total, "by_severity": by_severity}


def build_envelope(
    scanned_files: list[str],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "scanner": SCANNER_NAME,
        "version": __version__,
        "scanned_files": scanned_files,
        "findings": findings,
        "summary": build_summary(findings),
    }


def should_fail(fail_on: FailOn, summary: dict[str, Any]) -> bool:
    total = summary.get("total", 0)
    if total == 0:
        return False
    if fail_on == "none":
        return False
    if fail_on == "any":
        return True
    by_sev = summary.get("by_severity", {})
    return by_sev.get("critical", 0) > 0 or by_sev.get("high", 0) > 0


def format_human(report: dict[str, Any], quiet: bool = False) -> str:
    lines: list[str] = []
    if not quiet:
        lines.append(f"{SCANNER_NAME} v{report['version']}")
        lines.append(f"Scanned {len(report['scanned_files'])} file(s)")
        lines.append("")

    for finding in report["findings"]:
        lines.append(f"## {finding['file']}")
        for vuln in finding["vulnerabilities"]:
            lines.append(
                f"  - {finding['package']}=={finding['installed_version']}: "
                f"{vuln['id']} ({vuln['severity']})"
            )
        lines.append("")

    summary = report["summary"]
    by_sev = summary["by_severity"]
    lines.append(
        f"Summary: {summary['total']} vulnerability(ies) — "
        f"critical={by_sev['critical']}, high={by_sev['high']}, "
        f"medium={by_sev['medium']}, low={by_sev['low']}"
    )
    return "\n".join(lines).rstrip() + "\n"


def merge_sarif(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge multiple pip-audit SARIF documents into one report."""
    runs: list[Any] = []
    version = "2.1.0"
    for doc in documents:
        if not doc:
            continue
        if "$schema" in doc and "version" not in doc:
            version = doc.get("version", version)
        for run in doc.get("runs", []):
            runs.append(run)
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": version, "runs": runs}


def format_output(
    report: dict[str, Any],
    output_format: str,
    sarif_documents: list[dict[str, Any]] | None = None,
) -> str:
    if output_format == "json":
        return json.dumps(report, indent=2) + "\n"
    if output_format == "human":
        return format_human(report)
    if output_format == "sarif":
        merged = merge_sarif(sarif_documents or [])
        return json.dumps(merged, indent=2) + "\n"
    raise ValueError(f"Unsupported format: {output_format}")


def display_path(path: Path, root: Path | None) -> str:
    if root is not None:
        try:
            return str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            pass
    return str(path)

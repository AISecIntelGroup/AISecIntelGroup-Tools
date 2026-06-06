"""Format RAG audit reports."""

from __future__ import annotations

import json
from typing import Literal

from rag_audit_engine import SCANNER_NAME, __version__
from rag_audit_engine.models import AuditRecord

FailOn = Literal["threshold", "none"]


def build_summary(records: list[AuditRecord], fail_below: float) -> dict:
    total = len(records)
    failed = sum(1 for r in records if r.scores.overall < fail_below)
    avg = sum(r.scores.overall for r in records) / total if total else 0.0
    return {
        "total": total,
        "failed": failed,
        "avg_overall": round(avg, 4),
        "fail_below": fail_below,
    }


def build_envelope(records: list[AuditRecord], fail_below: float) -> dict:
    return {
        "scanner": SCANNER_NAME,
        "version": __version__,
        "records": [r.model_dump() for r in records],
        "summary": build_summary(records, fail_below),
    }


def should_fail(fail_on: FailOn, summary: dict) -> bool:
    if fail_on == "none":
        return False
    return summary.get("failed", 0) > 0


def format_human(report: dict, quiet: bool = False) -> str:
    lines: list[str] = []
    if not quiet:
        lines.append(f"{report['scanner']} v{report['version']}")
        lines.append("")

    for record in report["records"]:
        scores = record["scores"]
        lines.append(f"## Record {record['id']}")
        lines.append(
            f"  overall={scores['overall']:.2f} "
            f"grounded={scores['grounded']:.2f} "
            f"aligned={scores['aligned']:.2f} "
            f"risk={scores['hallucination_risk']}"
        )
        if record["flags"]:
            lines.append(f"  flags: {', '.join(record['flags'])}")
        if record.get("notes"):
            lines.append(f"  notes: {record['notes']}")
        lines.append("")

    summary = report["summary"]
    lines.append(
        f"Summary: {summary['total']} record(s), "
        f"{summary['failed']} below {summary['fail_below']}, "
        f"avg_overall={summary['avg_overall']:.2f}"
    )
    return "\n".join(lines).rstrip() + "\n"


def format_output(report: dict, output_format: str, quiet: bool = False) -> str:
    if output_format == "json":
        return json.dumps(report, indent=2) + "\n"
    if output_format == "human":
        return format_human(report, quiet=quiet)
    raise ValueError(f"Unsupported format: {output_format}")

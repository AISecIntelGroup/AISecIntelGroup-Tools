"""Format PromptGuard scan reports."""

from __future__ import annotations

import json
from typing import Literal

from prompt_guard import SCANNER_NAME, __version__
from prompt_guard.guard import ScanResult

FailOn = Literal["blocked", "none"]


def result_to_record(record_id: str, prompt: str, result: ScanResult) -> dict:
    reason = result.reason
    return {
        "id": record_id,
        "prompt": prompt,
        "blocked": result.blocked,
        "reason": reason.name if reason else None,
        "reason_detail": reason.value if reason else None,
        "matched_fragment": result.matched_fragment,
    }


def build_summary(records: list[dict]) -> dict:
    total = len(records)
    blocked = sum(1 for r in records if r["blocked"])
    return {
        "total": total,
        "blocked": blocked,
        "allowed": total - blocked,
    }


def build_envelope(records: list[dict]) -> dict:
    return {
        "scanner": SCANNER_NAME,
        "version": __version__,
        "records": records,
        "summary": build_summary(records),
    }


def should_fail(fail_on: FailOn, summary: dict) -> bool:
    if fail_on == "none":
        return False
    return summary.get("blocked", 0) > 0


def format_human(report: dict, quiet: bool = False) -> str:
    lines: list[str] = []
    if not quiet:
        lines.append(f"{report['scanner']} v{report['version']}")
        lines.append("")

    for record in report["records"]:
        status = "BLOCKED" if record["blocked"] else "ALLOWED"
        lines.append(f"## Record {record['id']} — {status}")
        if record["blocked"]:
            lines.append(f"  reason: {record['reason']}")
            lines.append(f"  detail: {record['reason_detail']}")
            if record.get("matched_fragment"):
                lines.append(f"  match: {record['matched_fragment']}")
        lines.append("")

    summary = report["summary"]
    lines.append(
        f"Summary: {summary['total']} prompt(s), "
        f"{summary['blocked']} blocked, {summary['allowed']} allowed"
    )
    return "\n".join(lines).rstrip() + "\n"


def format_output(report: dict, output_format: str, quiet: bool = False) -> str:
    if output_format == "json":
        return json.dumps(report, indent=2) + "\n"
    if output_format == "human":
        return format_human(report, quiet=quiet)
    raise ValueError(f"Unsupported format: {output_format}")

"""CLI for supply-chain-scanner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from supply_chain_scanner import audit
from supply_chain_scanner.discover import discover_requirements
from supply_chain_scanner.report import (
    FailOn,
    build_envelope,
    display_path,
    format_human,
    format_output,
    normalize_file_findings,
    should_fail,
)


def _resolve_targets(args: argparse.Namespace) -> list[Path]:
    if args.discover:
        return discover_requirements(args.root)
    req = args.requirements
    if req is None:
        default = Path("requirements.txt")
        return [default] if default.exists() else []
    return [req]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan Python requirements.txt files for known CVEs (OWASP LLM03)."
    )
    parser.add_argument(
        "-r",
        "--requirements",
        type=Path,
        default=None,
        help="Scan a single requirements file (default: ./requirements.txt if present)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root for --discover",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Find and scan all requirements.txt under --root",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("json", "human", "sarif"),
        default="json",
        help="Output format",
    )
    parser.add_argument("-o", "--output", type=Path, default=None, help="Write report to file")
    parser.add_argument(
        "--fail-on",
        choices=("any", "high", "none"),
        default="any",
        help="Exit 1 when findings meet this severity threshold",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress human-mode headers")
    args = parser.parse_args(argv)

    targets = _resolve_targets(args)
    if not targets:
        print("No requirements files found to scan.", file=sys.stderr)
        return 2

    missing = [p for p in targets if not p.exists()]
    if missing:
        for path in missing:
            print(f"Requirements file not found: {path}", file=sys.stderr)
        return 2

    fail_on: FailOn = args.fail_on
    display_root = args.root if args.discover else None
    all_findings: list[dict] = []
    scanned_files: list[str] = []
    sarif_documents: list[dict] = []

    pip_format = "sarif" if args.format == "sarif" else "json"
    for req_path in targets:
        rel = display_path(req_path, display_root)
        scanned_files.append(rel)
        if not args.quiet and args.format == "human":
            print(f"Scanning {rel}...", file=sys.stderr)
        try:
            raw = audit.audit_file(req_path, output_format=pip_format)
        except audit.AuditError as exc:
            print(str(exc), file=sys.stderr)
            return 3

        if args.format == "sarif":
            if isinstance(raw, dict):
                sarif_documents.append(raw)
        elif isinstance(raw, list):
            all_findings.extend(normalize_file_findings(rel, raw))

    report = build_envelope(scanned_files, all_findings)
    if args.format == "sarif":
        body = format_output(report, "sarif", sarif_documents=sarif_documents)
    elif args.format == "human":
        body = format_human(report, quiet=args.quiet)
    else:
        body = format_output(report, "json")

    if args.output:
        args.output.write_text(body)
    else:
        sys.stdout.write(body)

    if should_fail(fail_on, report["summary"]):
        return 1
    return 0

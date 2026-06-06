"""CLI for PromptGuard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from prompt_guard.batch import BatchInputError, load_batch_input
from prompt_guard.guard import PromptGuard
from prompt_guard.report import FailOn, build_envelope, format_output, result_to_record, should_fail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan prompts for injection and jailbreak patterns (OWASP LLM01)."
    )
    parser.add_argument("-p", "--prompt", help="Single prompt to scan")
    parser.add_argument("-i", "--input", type=Path, help="Batch JSON/JSONL input file")
    parser.add_argument(
        "-f",
        "--format",
        choices=("json", "human"),
        default="json",
        help="Output format",
    )
    parser.add_argument("-o", "--output", type=Path, help="Write report to file")
    parser.add_argument(
        "--fail-on",
        choices=("blocked", "none"),
        default="blocked",
        help="Exit 1 when any prompt is blocked",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress human-mode headers")
    args = parser.parse_args(argv)

    fail_on: FailOn = args.fail_on
    items: list[dict]

    if args.input:
        try:
            items = load_batch_input(args.input)
        except BatchInputError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    elif args.prompt is not None:
        items = [{"id": "1", "prompt": args.prompt}]
    else:
        print("Provide --prompt or --input for batch mode.", file=sys.stderr)
        return 2

    guard = PromptGuard()
    records = [
        result_to_record(item["id"], item["prompt"], guard.check(item["prompt"]))
        for item in items
    ]

    report = build_envelope(records)
    body = format_output(report, args.format, quiet=args.quiet)

    if args.output:
        args.output.write_text(body, encoding="utf-8")
    else:
        sys.stdout.write(body)

    if should_fail(fail_on, report["summary"]):
        return 1
    return 0

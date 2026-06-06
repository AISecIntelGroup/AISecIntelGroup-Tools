"""CLI for RAG audit engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rag_audit_engine.batch import BatchInputError, load_batch_input
from rag_audit_engine.report import FailOn, build_envelope, format_output, should_fail
from rag_audit_engine.scoring import score_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit RAG answers for grounding and alignment (OWASP LLM09)."
    )
    parser.add_argument("-c", "--context", help="Retrieved context (single mode)")
    parser.add_argument("-a", "--answer", help="Model answer (single mode)")
    parser.add_argument("--query", help="Optional user question for alignment scoring")
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
        "--fail-below",
        type=float,
        default=0.5,
        help="Exit 1 when any record overall score is below this threshold",
    )
    parser.add_argument(
        "--fail-on",
        choices=("threshold", "none"),
        default="threshold",
        help="Whether sub-threshold records fail the process",
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
    elif args.context is not None and args.answer is not None:
        items = [
            {
                "id": "1",
                "context": args.context,
                "answer": args.answer,
                "query": args.query,
            }
        ]
    else:
        print("Provide --context and --answer, or --input for batch mode.", file=sys.stderr)
        return 2

    records = [
        score_record(
            record_id=item["id"],
            context=item["context"],
            answer=item["answer"],
            query=item.get("query"),
        )
        for item in items
    ]

    report = build_envelope(records, args.fail_below)
    body = format_output(report, args.format, quiet=args.quiet)

    if args.output:
        args.output.write_text(body, encoding="utf-8")
    else:
        sys.stdout.write(body)

    if should_fail(fail_on, report["summary"]):
        return 1
    return 0

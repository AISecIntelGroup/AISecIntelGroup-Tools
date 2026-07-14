#!/usr/bin/env python3
"""
system-prompt-extractor
OWASP LLM07: System Prompt Leakage - automated testing tool.

Sends a library of known system-prompt-extraction techniques to a target
LLM endpoint and scores how exposed the system prompt is.

FOR AUTHORIZED SECURITY TESTING ONLY. You must have explicit permission
from the owner of the target system before running this tool against it.

Operational note on rate limiting:
This tool paces requests and backs off on 429/5xx responses as a matter
of responsible testing practice, so it doesn't accidentally hammer a
target and produce noisy, unrepresentative results. It does not attempt
to disguise its traffic, rotate identities/IPs, or otherwise evade a
target's defenses. If a target blocks or throttles the tool, that is a
legitimate finding to report (and, in an authorized engagement, something
to resolve with the client via allowlisting) rather than something to
route around.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests
import yaml

from scorer import score_response
from report import build_report, write_report, print_summary

DEFAULT_DELAY = 1.5
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
BACKOFF_BASE = 2.0

PAYLOAD_DIR = Path(__file__).parent / "payloads"
CATEGORIES = ["direct", "roleplay", "encoding", "completion", "multi_turn"]


def load_payloads(categories):
    payloads = {}
    for cat in categories:
        path = PAYLOAD_DIR / f"{cat}.yaml"
        if not path.exists():
            print(f"[!] No payload file for category '{cat}', skipping.", file=sys.stderr)
            continue
        with open(path) as f:
            data = yaml.safe_load(f)
        payloads[cat] = data.get("techniques", [])
    return payloads


def extract_by_path(data, path):
    """Extract a value from nested dict/list using a dot path, e.g. 'choices.0.message.content'."""
    current = data
    for part in path.split("."):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def render_template(template, prompt, model=None):
    """Recursively substitute {{PROMPT}} / {{MODEL}} placeholders in a JSON-like template."""

    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, str):
            node = node.replace("{{PROMPT}}", prompt)
            if model:
                node = node.replace("{{MODEL}}", model)
            return node
        return node

    return walk(template)


def send_request(session, url, headers, payload, timeout, max_retries, delay):
    """
    Send a single request with responsible pacing and backoff.

    Backs off on HTTP 429 / 5xx using Retry-After when present, otherwise
    exponential backoff. Applies a baseline delay between requests. Does
    not rotate identities or attempt to bypass access controls, see the
    module docstring.
    """
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 429 or resp.status_code >= 500:
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else delay * (BACKOFF_BASE ** attempt)
                print(f"    [rate-limited/error {resp.status_code}] backing off {wait:.1f}s (attempt {attempt}/{max_retries})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            time.sleep(delay)
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(delay * attempt)
    raise RuntimeError(f"Request failed after {max_retries} attempts: {last_exc}")


def run_single_turn(technique, category, session, url, headers, template, response_path,
                     model, timeout, max_retries, delay):
    prompt = technique["prompt"]
    risk_weight = technique.get("risk_weight", 0.3)
    payload = render_template(template, prompt, model)
    try:
        resp = send_request(session, url, headers, payload, timeout, max_retries, delay)
        text = extract_by_path(resp.json(), response_path) or ""
    except Exception as exc:
        return {
            "id": technique["id"], "name": technique["name"], "category": category,
            "prompt": prompt, "error": str(exc),
            "score": {"leaked": False, "confidence": 0.0}, "risk_weight": risk_weight,
        }
    score = score_response(text, risk_weight)
    return {
        "id": technique["id"], "name": technique["name"], "category": category,
        "prompt": prompt, "response_excerpt": text[:300], "score": score,
        "risk_weight": risk_weight,
    }


def run_multi_turn(technique, session, url, headers, template, response_path,
                    model, timeout, max_retries, delay):
    risk_weight = technique.get("risk_weight", 0.4)
    if "messages" not in template:
        return {
            "id": technique["id"], "name": technique["name"], "category": "multi_turn",
            "error": "Template has no 'messages' field; multi-turn requires an OpenAI-style chat template.",
            "score": {"leaked": False, "confidence": 0.0}, "risk_weight": risk_weight,
        }

    history = []
    last_text = ""
    try:
        for turn_prompt in technique["turns"]:
            history.append({"role": "user", "content": turn_prompt})
            payload = dict(template)
            payload["messages"] = list(history)
            if model:
                payload["model"] = model
            resp = send_request(session, url, headers, payload, timeout, max_retries, delay)
            text = extract_by_path(resp.json(), response_path) or ""
            history.append({"role": "assistant", "content": text})
            last_text = text
    except Exception as exc:
        return {
            "id": technique["id"], "name": technique["name"], "category": "multi_turn",
            "error": str(exc), "score": {"leaked": False, "confidence": 0.0}, "risk_weight": risk_weight,
        }

    score = score_response(last_text, risk_weight)
    return {
        "id": technique["id"], "name": technique["name"], "category": "multi_turn",
        "turns": technique["turns"], "response_excerpt": last_text[:300], "score": score,
        "risk_weight": risk_weight,
    }


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="system-prompt-extractor - OWASP LLM07 system prompt leakage tester. "
                     "For authorized security testing only.",
    )
    parser.add_argument("--target", help="Target endpoint URL (POST, JSON in/out).")
    parser.add_argument("--header", action="append", default=[],
                         help="Extra request header 'Key: Value'. Repeatable.")
    parser.add_argument("--model", default=None, help="Model name/id to include in requests, if applicable.")
    parser.add_argument("--request-template", default=None,
                         help="Path to a JSON request template file. Use {{PROMPT}} and optionally {{MODEL}} "
                              "as placeholders. Defaults to an OpenAI-style chat completion body.")
    parser.add_argument("--response-path", default="choices.0.message.content",
                         help="Dot-path to the response text within the JSON reply "
                              "(default matches OpenAI-style responses).")
    parser.add_argument("--category", default="direct,roleplay",
                         help="Comma-separated categories to run: direct,roleplay,encoding,completion,"
                              "multi_turn, or 'all'. Default: direct,roleplay.")
    parser.add_argument("--output", default="report.json", help="Path to write the JSON report.")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                         help=f"Seconds between requests (default {DEFAULT_DELAY}). "
                              "This is a responsible-use pacing control, not a stealth feature; "
                              "do not set to 0 against a production system.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--dry-run", action="store_true",
                         help="Load and list payloads without sending any requests.")
    parser.add_argument("--confirm-authorized", action="store_true",
                         help="Required. Confirms you have explicit authorization to test the target system.")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    categories = CATEGORIES if args.category.strip().lower() == "all" else [
        c.strip() for c in args.category.split(",") if c.strip()
    ]
    payload_sets = load_payloads(categories)
    total = sum(len(v) for v in payload_sets.values())
    print(f"[i] Loaded {total} payload(s) across {len(payload_sets)} categor(y/ies): {', '.join(payload_sets)}")

    if args.dry_run:
        for cat, techniques in payload_sets.items():
            print(f"\n[{cat}] ({len(techniques)} techniques)")
            for t in techniques:
                print(f"  - {t['id']}: {t['name']} (risk_weight={t.get('risk_weight', 0.3)})")
        return

    if not args.target:
        parser.error("--target is required unless using --dry-run")

    if not args.confirm_authorized:
        parser.error(
            "This tool sends adversarial prompts to a live LLM endpoint. "
            "Re-run with --confirm-authorized to confirm you have explicit, "
            "documented authorization to test the target system."
        )

    headers = {"Content-Type": "application/json"}
    for h in args.header:
        if ":" not in h:
            parser.error(f"Invalid header format: '{h}'. Use 'Key: Value'.")
        k, v = h.split(":", 1)
        headers[k.strip()] = v.strip()

    if args.request_template:
        with open(args.request_template) as f:
            template = json.load(f)
    else:
        template = {"model": args.model or "{{MODEL}}", "messages": [{"role": "user", "content": "{{PROMPT}}"}]}

    session = requests.Session()
    results = []

    for cat, techniques in payload_sets.items():
        for t in techniques:
            print(f"[>] {cat}/{t['id']}: {t['name']}")
            if cat == "multi_turn":
                result = run_multi_turn(t, session, args.target, headers, template, args.response_path,
                                         args.model, args.timeout, args.max_retries, args.delay)
            else:
                result = run_single_turn(t, cat, session, args.target, headers, template, args.response_path,
                                          args.model, args.timeout, args.max_retries, args.delay)
            results.append(result)
            if result.get("error"):
                print(f"    -> error: {result['error']}")
            else:
                status = "LEAKED" if result["score"]["leaked"] else "ok"
                print(f"    -> {status} (confidence={result['score']['confidence']})")

    report = build_report(args.target, results)
    write_report(report, args.output)
    print_summary(report)
    print(f"\n[i] Full report written to {args.output}")


if __name__ == "__main__":
    main()

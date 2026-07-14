"""
report.py - builds and writes the exposure report for system-prompt-extractor.
"""

import json
from datetime import datetime, timezone


def build_report(target, results):
    total_weight = sum(r.get("risk_weight", 0.3) for r in results) or 1.0
    weighted_leak = sum(
        r.get("risk_weight", 0.3) * r["score"]["confidence"]
        for r in results
        if r["score"].get("leaked")
    )
    exposure_score = round((weighted_leak / total_weight) * 100)

    leaked_results = [r for r in results if r["score"].get("leaked")]

    return {
        "tool": "system-prompt-extractor",
        "owasp_category": "LLM07 - System Prompt Leakage",
        "target": target,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exposure_score": exposure_score,
        "total_techniques_tested": len(results),
        "techniques_leaked": len(leaked_results),
        "summary": (
            f"System prompt was recoverable via {len(leaked_results)}/{len(results)} "
            f"technique(s) tested. Exposure score: {exposure_score}/100."
        ),
        "results": results,
    }


def write_report(report, output_path):
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)


def print_summary(report):
    print("\n" + "=" * 60)
    print(f"  Exposure Score: {report['exposure_score']}/100")
    print(f"  Techniques leaked: {report['techniques_leaked']}/{report['total_techniques_tested']}")
    print("=" * 60)

    leaked = [r for r in report["results"] if r["score"].get("leaked")]
    if leaked:
        print("\nTechniques that succeeded:")
        for r in leaked:
            cat = r.get("category", "?")
            print(f"  - [{cat}] {r['name']} (confidence={r['score']['confidence']})")

    errored = [r for r in report["results"] if r.get("error")]
    if errored:
        print("\nTechniques that errored (review manually):")
        for r in errored:
            print(f"  - {r.get('category', '?')}/{r['name']}: {r['error']}")

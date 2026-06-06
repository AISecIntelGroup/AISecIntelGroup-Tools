from supply_chain_scanner.report import (
    build_envelope,
    build_summary,
    merge_sarif,
    normalize_file_findings,
    should_fail,
)

SAMPLE_RAW = [
    {
        "name": "insecure-package",
        "version": "1.0.0",
        "vulns": [
            {
                "id": "CVE-2024-0001",
                "description": "test",
                "cvss_score": 8.5,
            }
        ],
    }
]


def test_normalize_file_findings() -> None:
    findings = normalize_file_findings("req.txt", SAMPLE_RAW)
    assert len(findings) == 1
    assert findings[0]["package"] == "insecure-package"
    assert findings[0]["vulnerabilities"][0]["severity"] == "high"


def test_should_fail_any_and_high() -> None:
    summary = build_summary(normalize_file_findings("f", SAMPLE_RAW))
    assert should_fail("any", summary) is True
    assert should_fail("high", summary) is True
    assert should_fail("none", summary) is False


def test_should_fail_high_ignores_medium() -> None:
    raw = [
        {
            "name": "pkg",
            "version": "1.0.0",
            "vulns": [{"id": "CVE-1", "description": "x", "cvss_score": 5.0}],
        }
    ]
    summary = build_summary(normalize_file_findings("f", raw))
    assert should_fail("any", summary) is True
    assert should_fail("high", summary) is False


def test_build_envelope_schema() -> None:
    findings = normalize_file_findings("tools/x/requirements.txt", SAMPLE_RAW)
    report = build_envelope(["tools/x/requirements.txt"], findings)
    assert report["scanner"] == "aisecintel-supply-chain-scanner"
    assert report["version"] == "0.1.0"
    assert report["summary"]["total"] == 1


def test_merge_sarif_combines_runs() -> None:
    doc_a = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "a"}}}]}
    doc_b = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "b"}}}]}
    merged = merge_sarif([doc_a, doc_b])
    assert len(merged["runs"]) == 2

import json
import os
import tempfile
import unittest

from report import build_report, print_summary, write_report
from tests.helpers import capture_output


def make_result(id_, category, name, leaked, confidence, risk_weight, error=None):
    result = {
        "id": id_,
        "name": name,
        "category": category,
        "risk_weight": risk_weight,
        "score": {"leaked": leaked, "confidence": confidence},
    }
    if error:
        result["error"] = error
    return result


class TestBuildReport(unittest.TestCase):
    def test_all_leaked_gives_full_exposure(self):
        results = [
            make_result("d1", "direct", "plain_ask", True, 1.0, 0.5),
            make_result("d2", "direct", "debug_mode", True, 1.0, 0.5),
        ]
        report = build_report("https://example.com", results)
        self.assertEqual(report["exposure_score"], 100)
        self.assertEqual(report["techniques_leaked"], 2)
        self.assertEqual(report["total_techniques_tested"], 2)

    def test_none_leaked_gives_zero_exposure(self):
        results = [
            make_result("d1", "direct", "plain_ask", False, 0.0, 0.5),
            make_result("d2", "direct", "debug_mode", False, 0.1, 0.5),
        ]
        report = build_report("https://example.com", results)
        self.assertEqual(report["exposure_score"], 0)
        self.assertEqual(report["techniques_leaked"], 0)

    def test_weights_partial_leaks_correctly(self):
        results = [
            make_result("d1", "direct", "a", True, 1.0, 0.75),  # leaked, weight 0.75
            make_result("d2", "direct", "b", False, 0.2, 0.25),  # not leaked, weight 0.25
        ]
        report = build_report("https://example.com", results)
        # weighted_leak = 0.75 * 1.0 = 0.75; total_weight = 1.0 -> 75/100
        self.assertEqual(report["exposure_score"], 75)

    def test_handles_empty_results(self):
        report = build_report("https://example.com", [])
        self.assertEqual(report["exposure_score"], 0)
        self.assertEqual(report["total_techniques_tested"], 0)
        self.assertEqual(report["techniques_leaked"], 0)

    def test_includes_owasp_category_and_target(self):
        report = build_report("https://target.test", [])
        self.assertEqual(report["owasp_category"], "LLM07 - System Prompt Leakage")
        self.assertEqual(report["target"], "https://target.test")

    def test_summary_mentions_counts(self):
        results = [make_result("d1", "direct", "plain_ask", True, 0.9, 0.5)]
        report = build_report("https://example.com", results)
        self.assertIn("1/1", report["summary"])


class TestWriteReport(unittest.TestCase):
    def test_produces_valid_reloadable_json(self):
        report = build_report("https://example.com", [make_result("d1", "direct", "a", True, 0.9, 0.5)])
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.json")
            write_report(report, out_path)
            with open(out_path) as f:
                loaded = json.load(f)
        self.assertEqual(loaded["exposure_score"], report["exposure_score"])
        self.assertEqual(loaded["target"], "https://example.com")


class TestPrintSummary(unittest.TestCase):
    def test_lists_leaked_techniques_only(self):
        results = [
            make_result("d1", "direct", "plain_ask", True, 0.9, 0.5),
            make_result("d2", "direct", "debug_mode", False, 0.0, 0.5),
        ]
        report = build_report("https://example.com", results)
        with capture_output() as (out, _err):
            print_summary(report)
        text = out.getvalue()
        self.assertIn("Exposure Score", text)
        self.assertIn("plain_ask", text)
        self.assertNotIn("debug_mode", text)  # only leaked techniques are listed

    def test_lists_errored_techniques(self):
        results = [make_result("d1", "direct", "plain_ask", False, 0.0, 0.5, error="timeout")]
        report = build_report("https://example.com", results)
        with capture_output() as (out, _err):
            print_summary(report)
        self.assertIn("timeout", out.getvalue())


if __name__ == "__main__":
    unittest.main()
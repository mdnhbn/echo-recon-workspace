"""Local Nuclei engine/template readiness checks; no network or target scans."""
import unittest
from unittest.mock import patch

from echo_recon.runner import Result
from echo_recon.tools import diagnostics, nuclei_templates_incomplete


class NucleiTemplateHealthTests(unittest.TestCase):
    def run_health(self, template_result):
        help_result = Result("done", 0,
                             "nuclei -jsonl -disable-redirects -exclude-tags", "", 0.01)
        calls = []

        def fake_run(args, **kwargs):
            calls.append((args, kwargs))
            return help_result if len(calls) == 1 else template_result

        def resolve(name):
            return ("nuclei",) if name == "nuclei" else None

        with patch("echo_recon.tools.resolve_tool", side_effect=resolve), \
             patch("echo_recon.tools.run", side_effect=fake_run):
            result = diagnostics()
        return result["nuclei"], calls

    def test_templates_version_is_checked_without_auto_update(self):
        item, calls = self.run_health(Result(
            "done", 0, "[INF] Public nuclei-templates version: v10.5.0 (/home/user/nuclei-templates)", "", 0.01))
        self.assertEqual(item["status"], "ready")
        self.assertEqual(item["engine_status"], "ready")
        self.assertEqual(item["template_status"], "ready")
        self.assertEqual(item["template_version"], "v10.5.0")
        self.assertTrue(calls[1][0][-2:] == ["-tv", "-duc"])
        self.assertFalse(nuclei_templates_incomplete({"nuclei": item}))

    def test_missing_template_metadata_is_reported_separately_from_engine(self):
        item, _ = self.run_health(Result("done", 0, "[INF] Nuclei Engine Version: v3.11.1", "", 0.01))
        self.assertEqual(item["status"], "unverified")
        self.assertEqual(item["engine_status"], "ready")
        self.assertEqual(item["template_status"], "missing")
        self.assertTrue(nuclei_templates_incomplete({"nuclei": item}))

    def test_failed_template_query_does_not_claim_data_is_missing(self):
        item, _ = self.run_health(Result("timeout", None, "", "template check timed out", 10))
        self.assertEqual(item["engine_status"], "ready")
        self.assertEqual(item["template_status"], "unverified")
        self.assertTrue(nuclei_templates_incomplete({"nuclei": item}))


if __name__ == "__main__":
    unittest.main()

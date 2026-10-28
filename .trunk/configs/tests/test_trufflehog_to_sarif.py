"""Exercise the filesystem JSONL reader through its command-line boundary."""

import base64
import json
import os
import subprocess  # nosec B404 - CLI boundary coverage requires subprocess.
import sys
import tempfile
import unittest
from pathlib import Path

READER = Path(
    os.environ.get(
        "TRUFFLEHOG_READER",
        str(Path(__file__).resolve().parents[1] / "trufflehog_to_sarif.py"),
    )
)


class TruffleHogReaderTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def fixture(self, name, content):
        fixture = Path(self.directory.name) / name
        if isinstance(content, bytes):
            fixture.write_bytes(content)
        else:
            fixture.write_text(content, encoding="utf-8")
        return str(fixture)

    def finding(self, filename, raw="synthetic-secret"):
        return {
            "DetectorName": "Github",
            "Raw": raw,
            "Redacted": raw,
            "SourceMetadata": {"Data": {"Filesystem": {"file": filename}}},
        }

    def invoke(self, input_text):
        return subprocess.run(  # nosec B603 - Test-controlled argv; JSON uses stdin.
            [sys.executable, str(READER)],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def convert(self, findings):
        completed = self.invoke("".join(json.dumps(item) + "\n" for item in findings))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)["runs"][0]["results"]

    def location(self, result):
        return result["locations"][0]["physicalLocation"]

    def test_encoded_finding_survives_without_literal_location(self):
        raw = "synthetic-secret"
        filename = self.fixture("encoded.txt", base64.b64encode(raw.encode()).decode())
        results = self.convert([self.finding(filename, raw)])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["ruleId"], "Github")
        self.assertEqual(self.location(results[0])["artifactLocation"]["uri"], filename)
        self.assertNotIn("region", self.location(results[0]))

    def test_literal_location_is_one_based(self):
        filename = self.fixture("literal.txt", "header\nprefix synthetic-secret\n")
        results = self.convert([self.finding(filename)])
        region = self.location(results[0])["region"]
        self.assertEqual(region["startLine"], 2)
        self.assertEqual(region["startColumn"], 8)

    def test_multiline_location_starts_at_first_literal_character(self):
        filename = self.fixture("multiline.txt", "header\nprefix first\nsecond\n")
        results = self.convert([self.finding(filename, "first\nsecond")])
        region = self.location(results[0])["region"]
        self.assertEqual(region["startLine"], 2)
        self.assertEqual(region["startColumn"], 8)

    def test_repeated_occurrences_and_files_do_not_share_location_state(self):
        first = self.fixture("first.txt", "synthetic-secret\nsynthetic-secret\n")
        second = self.fixture("second.txt", "synthetic-secret\n")
        results = self.convert(
            [
                self.finding(first),
                self.finding(first),
                self.finding(second),
                self.finding(first),
            ]
        )
        self.assertEqual(len(results), 4)
        self.assertEqual(
            [self.location(result)["region"]["startLine"] for result in results[:3]],
            [1, 2, 1],
        )
        self.assertNotIn("region", self.location(results[3]))

    def test_different_secrets_in_one_file_keep_independent_locations(self):
        filename = self.fixture("secrets.txt", "first-secret second-secret")
        results = self.convert(
            [
                self.finding(filename, "first-secret"),
                self.finding(filename, "second-secret"),
            ]
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(
            [self.location(result)["region"]["startColumn"] for result in results],
            [1, 14],
        )

    def test_messages_do_not_expose_raw_or_redacted_values(self):
        filename = self.fixture("message.txt", "synthetic-secret")
        results = self.convert([self.finding(filename)])
        self.assertEqual(results[0]["message"]["text"], "Secret detected")
        self.assertNotIn("synthetic-secret", json.dumps(results))

    def test_unreadable_and_binary_files_keep_file_level_findings(self):
        unreadable = str(Path(self.directory.name) / "missing.txt")
        binary = self.fixture("binary.txt", b"\xff\xfe")
        for filename in [unreadable, binary, self.directory.name]:
            with self.subTest(filename=filename):
                results = self.convert([self.finding(filename)])
                self.assertEqual(len(results), 1)
                self.assertNotIn("region", self.location(results[0]))

    def test_empty_raw_value_keeps_file_level_finding(self):
        filename = self.fixture("empty.txt", "content")
        results = self.convert([self.finding(filename, "")])
        self.assertEqual(len(results), 1)
        self.assertNotIn("region", self.location(results[0]))

    def test_blank_input_is_clean_sarif(self):
        completed = self.invoke("\n  \n")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["runs"][0]["results"], [])

    def test_invalid_input_fails_without_emitting_clean_sarif_or_secret(self):
        finding = self.finding("unused.txt")
        for invalid in [
            "{malformed synthetic-secret",
            "[]",
            "null",
            "{}",
            json.dumps({**finding, "SourceMetadata": {"Data": {"Git": {"file": "x"}}}}),
            json.dumps({**finding, "SourceMetadata": {"Data": {"Filesystem": {}}}}),
            json.dumps({**finding, "DetectorName": ""}),
            json.dumps({**finding, "Raw": None}),
        ]:
            with self.subTest(invalid=invalid):
                completed = self.invoke(json.dumps(finding) + "\n" + invalid + "\n")
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(completed.stdout, "")
                self.assertTrue(completed.stderr)
                self.assertNotIn("synthetic-secret", completed.stderr)


if __name__ == "__main__":
    unittest.main()

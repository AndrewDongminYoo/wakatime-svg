"""Exercise the filesystem JSONL reader through its command-line boundary."""

import base64
import json
import os
import subprocess  # nosec B404 - Tests invoke only the local reader with a fixed interpreter.
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
        return subprocess.run(  # nosec B603 - Fixed interpreter and reader; no shell.
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

    def measured_results(self, findings):
        wrapper = (
            "import runpy, sys, tracemalloc\n"
            "tracemalloc.start()\n"
            "try:\n"
            "    runpy.run_path(sys.argv[1], run_name='__main__')\n"
            "finally:\n"
            "    print('reader_peak_bytes=' + str(tracemalloc.get_traced_memory()[1]), file=sys.stderr)\n"
        )
        completed = subprocess.run(  # nosec B603 - Fixed trace wrapper; no shell.
            [sys.executable, "-c", wrapper, str(READER)],
            input="".join(json.dumps(item) + "\n" for item in findings),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        peak = int(completed.stderr.rpartition("reader_peak_bytes=")[2].strip())
        return json.loads(completed.stdout)["runs"][0]["results"], peak

    def location(self, result):
        return result["locations"][0]["physicalLocation"]

    def test_unicode_code_point_columns_are_declared(self):
        filename = self.fixture("unicode-columns.txt", "😀 synthetic-secret\n")
        completed = self.invoke(json.dumps(self.finding(filename)) + "\n")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        run = json.loads(completed.stdout)["runs"][0]
        self.assertEqual(run.get("columnKind"), "unicodeCodePoints")
        self.assertEqual(
            self.location(run["results"][0])["region"],
            {"startLine": 1, "startColumn": 3},
        )

    def test_reserved_filename_remains_a_native_trunk_path(self):
        filename = self.fixture("space #50% 한글.txt", "synthetic-secret\n")
        result = self.convert([self.finding(filename)])[0]
        emitted = self.location(result)["artifactLocation"]["uri"]
        self.assertEqual(emitted, filename)
        self.assertTrue(Path(emitted).samefile(filename))

    def test_large_source_keeps_a_file_level_finding(self):
        filename = self.fixture(
            "large.txt", "synthetic-secret\n" + "x" * (32 * 1024 * 1024)
        )
        results, peak = self.measured_results([self.finding(filename)])
        self.assertLess(peak, 16 * 1024 * 1024)
        self.assertEqual(len(results), 1)
        location = self.location(results[0])
        self.assertEqual(location["artifactLocation"]["uri"], filename)
        self.assertNotIn("region", location)

    def test_source_cache_memory_is_bounded_and_offsets_survive_eviction(self):
        findings = []
        filler = "x" * (768 * 1024)
        for index in range(32):
            prefix = "synthetic-secret\n" * (2 if index == 0 else 1)
            filename = self.fixture(f"cache-{index}.txt", prefix + filler)
            findings.append(self.finding(filename))
        findings.append(findings[0])
        results, peak = self.measured_results(findings)
        self.assertLess(peak, 16 * 1024 * 1024)
        self.assertEqual(len(results), len(findings))
        self.assertEqual(self.location(results[0])["region"]["startLine"], 1)
        self.assertEqual(self.location(results[-1])["region"]["startLine"], 2)

    def test_encoded_finding_survives_without_literal_location(self):
        raw = "synthetic-secret"
        filename = self.fixture("encoded.txt", base64.b64encode(raw.encode()).decode())
        results = self.convert([self.finding(filename, raw)])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["ruleId"], "Github")
        self.assertEqual(self.location(results[0])["artifactLocation"]["uri"], filename)
        self.assertNotIn("region", self.location(results[0]))

    def test_reported_source_line_selects_the_matching_occurrence(self):
        filename = self.fixture(
            "reported.txt", "header\nsynthetic-secret\nspacer\nsynthetic-secret\n"
        )
        finding = self.finding(filename)
        finding["SourceMetadata"]["Data"]["Filesystem"]["line"] = 4
        results = self.convert([finding])
        self.assertEqual(self.location(results[0])["region"]["startLine"], 4)
        self.assertEqual(self.location(results[0])["region"]["startColumn"], 1)

    def test_reported_source_lines_can_arrive_out_of_order(self):
        filename = self.fixture(
            "reported-order.txt", "header\nsynthetic-secret\nspacer\nsynthetic-secret\n"
        )
        findings = [self.finding(filename), self.finding(filename)]
        for index, line in enumerate([4, 2]):
            findings[index]["SourceMetadata"]["Data"]["Filesystem"]["line"] = line
        results = self.convert(findings)
        self.assertEqual(
            [self.location(result)["region"]["startLine"] for result in results], [4, 2]
        )

    def test_invalid_or_wrong_reported_line_keeps_literal_fallback(self):
        filename = self.fixture("reported-invalid.txt", "header\nsynthetic-secret\n")
        for line in [None, True, False, 0, -1, "2", 99, 1, {}]:
            with self.subTest(line=line):
                finding = self.finding(filename)
                finding["SourceMetadata"]["Data"]["Filesystem"]["line"] = line
                result = self.convert([finding])[0]
                self.assertEqual(self.location(result)["region"]["startLine"], 2)
                self.assertEqual(self.location(result)["region"]["startColumn"], 1)

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

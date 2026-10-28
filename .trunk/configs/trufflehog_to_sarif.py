#!/usr/bin/env python3
"""Convert offline TruffleHog filesystem JSONL without discarding findings."""

import json
import sys
from pathlib import Path


def physical_location(filename, secret, files, offsets):
    location = {"artifactLocation": {"uri": filename}}
    if filename not in files:
        try:
            with Path(filename).open(encoding="utf-8", newline="") as source:
                files[filename] = source.read()
        except OSError, UnicodeError, ValueError:
            files[filename] = None
    content = files[filename]
    if not secret or content is None:
        return location

    key = (filename, secret)
    position = content.find(secret, offsets.get(key, 0))
    if position >= 0:
        offsets[key] = position + 1
        location["region"] = {
            "startLine": content.count("\n", 0, position) + 1,
            "startColumn": position - content.rfind("\n", 0, position),
        }
    return location


def to_result(finding, files, offsets):
    if not isinstance(finding, dict):
        raise ValueError("expected an object")
    detector = finding.get("DetectorName")
    secret = finding.get("Raw")
    if not isinstance(detector, str) or not detector.strip():
        raise ValueError("expected a detector name")
    if not isinstance(secret, str):
        raise ValueError("expected a raw string")
    metadata = finding.get("SourceMetadata")
    data = metadata.get("Data") if isinstance(metadata, dict) else None
    filesystem = data.get("Filesystem") if isinstance(data, dict) else None
    filename = filesystem.get("file") if isinstance(filesystem, dict) else None
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("expected filesystem file metadata")

    return {
        "level": "error",
        "ruleId": detector,
        "message": {"text": "Secret detected"},
        "locations": [
            {"physicalLocation": physical_location(filename, secret, files, offsets)}
        ],
    }


def main():
    results = []
    files = {}
    offsets = {}
    for line_number, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        try:
            results.append(to_result(json.loads(line), files, offsets))
        except ValueError:
            print(
                f"Invalid TruffleHog filesystem JSONL at line {line_number}",
                file=sys.stderr,
            )
            return 1
    print(
        json.dumps(
            {
                "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
                "version": "2.1.0",
                "runs": [
                    {"tool": {"driver": {"name": "TruffleHog"}}, "results": results}
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Convert offline TruffleHog filesystem JSONL for Trunk's SARIF consumer."""

import json
import sys
from pathlib import Path

MAX_SOURCE_BYTES = 1024 * 1024
MAX_CACHED_FILES = 8


def physical_location(filename, secret, line_hint, files, offsets):
    # Trunk 1.25.0 resolves this as a native path and drops URI-escaped paths.
    location = {"artifactLocation": {"uri": filename}}
    if not secret:
        return location
    if filename not in files:
        if len(files) >= MAX_CACHED_FILES:
            files.pop(next(iter(files)))
        try:
            with Path(filename).open("rb") as source:
                data = source.read(MAX_SOURCE_BYTES + 1)
            files[filename] = (
                data.decode("utf-8") if len(data) <= MAX_SOURCE_BYTES else None
            )
        except (OSError, UnicodeError, ValueError):
            files[filename] = None
    content = files[filename]
    if content is None:
        return location

    position = -1
    if isinstance(line_hint, int) and not isinstance(line_hint, bool) and line_hint > 0:
        line_start = 0
        for _ in range(line_hint - 1):
            newline = content.find("\n", line_start)
            if newline < 0:
                break
            line_start = newline + 1
        else:
            candidate = content.find(secret, line_start)
            line_end = content.find("\n", line_start)
            if candidate >= 0 and (line_end < 0 or candidate <= line_end):
                position = candidate

    if position < 0:
        key = (filename, secret)
        position = content.find(secret, offsets.get(key, 0))
        if position >= 0:
            offsets[key] = position + 1
    if position >= 0:
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
            {
                "physicalLocation": physical_location(
                    filename, secret, filesystem.get("line"), files, offsets
                )
            }
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
                    {
                        "tool": {"driver": {"name": "TruffleHog"}},
                        "columnKind": "unicodeCodePoints",
                        "results": results,
                    }
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

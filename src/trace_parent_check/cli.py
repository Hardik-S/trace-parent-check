"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys

from .core import InvalidInput, validate_bytes


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="trace-parent-check",
        description="Check normalized trace parent references and cycles in JSONL.",
    )
    parser.add_argument("spans_jsonl", metavar="SPANS.jsonl", help="input file")
    args = parser.parse_args()
    try:
        with open(args.spans_jsonl, "rb") as stream:
            result = validate_bytes(stream.read())
    except (OSError, InvalidInput):
        sys.stdout.write('{"status":"invalid_input"}\n')
        return 2
    # Findings contain no IDs, so ASCII escaping also keeps stdout safe on
    # Windows consoles with legacy encodings.
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
    return 1 if result["status"] == "violations" else 0


if __name__ == "__main__":
    raise SystemExit(main())

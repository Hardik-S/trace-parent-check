# Trace Parent Check

`trace-parent-check` is a small offline validator for normalized span JSONL. It checks parent references and reports precisely which records belong to parent cycles. It does not inspect telemetry providers, runtime behavior, timing, or trace completeness.

## Install and run

Requires Python 3.10 or newer. From a fresh checkout:

```console
python -m venv .venv
# Activate the environment, then:
python -m pip install -e ".[test]"
trace-parent-check examples/valid.jsonl
```

The module form also works: `python -m trace_parent_check.cli examples/valid.jsonl`.

## Input

Each UTF-8 JSONL record must contain exactly `id` and `parent`. `id` is a unique, nonempty string. `parent` is either `null` or a nonempty string. Parents may occur before or after children; multiple roots are allowed. Empty input is valid. LF, CRLF, and CR line endings are accepted. Blank lines, duplicate JSON keys, duplicate IDs, extra or missing fields, malformed JSON, invalid UTF-8, and non-finite numbers invalidate the entire input.

The examples demonstrate the three outcomes:

```console
trace-parent-check examples/valid.jsonl
# exit 0: {"status":"valid", ...}
trace-parent-check examples/violations.jsonl
# exit 1: missing parent and cycle-member findings; cycle-tail is not a cycle member
trace-parent-check examples/invalid.jsonl
# exit 2: {"status":"invalid_input"}
```

Successful analysis emits one JSON object with `status`, `record_count`, `root_count`, and line-sorted `findings`. Dangling parents yield `missing_parent`. Every member of a directed cycle, including a self-parent, yields `cycle`; incoming tails do not. Invalid input always produces exactly `{"status":"invalid_input"}` on stdout with empty stderr. Input IDs and source text are never included in output.

Exit codes: `0` valid input without findings, `1` valid input with findings, `2` invalid or unreadable input. `--help` displays usage.

## Development

```console
python -m pip install -e ".[test]"
python -m pytest
```

The implementation uses only the Python standard library at runtime, and detects cycles iteratively so long chains do not depend on Python's recursion limit.

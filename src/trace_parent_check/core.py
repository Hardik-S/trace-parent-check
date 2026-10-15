"""Strict JSONL parsing and iterative trace-parent validation."""

from __future__ import annotations

import json
from typing import Any


class InvalidInput(ValueError):
    """Raised when the complete input is not valid normalized JSONL."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise InvalidInput("non-finite JSON number")


def validate_bytes(data: bytes) -> dict[str, Any]:
    """Validate UTF-8 JSONL bytes and return the contract result object."""
    try:
        source = data.decode("utf-8", errors="strict")
        rows: list[tuple[int, str, str | None]] = []
        seen: set[str] = set()
        # Recognize exactly the JSONL newline forms named in the contract.
        # str.splitlines() would also treat Unicode separators as boundaries.
        normalized = source.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        for line_number, line in enumerate(lines, start=1):
            if line_number == len(lines) and line == "":
                break  # A final line terminator does not create a blank record.
            if not line.strip():
                raise InvalidInput("blank line")
            try:
                value = json.loads(
                    line,
                    object_pairs_hook=_unique_object,
                    parse_constant=_reject_constant,
                )
            except (json.JSONDecodeError, RecursionError) as exc:
                raise InvalidInput("malformed JSON") from exc
            if not isinstance(value, dict) or set(value) != {"id", "parent"}:
                raise InvalidInput("wrong fields")
            identifier, parent = value["id"], value["parent"]
            if not isinstance(identifier, str) or not identifier:
                raise InvalidInput("invalid id")
            if parent is not None and (not isinstance(parent, str) or not parent):
                raise InvalidInput("invalid parent")
            if identifier in seen:
                raise InvalidInput("duplicate id")
            seen.add(identifier)
            rows.append((line_number, identifier, parent))
    except UnicodeDecodeError as exc:
        raise InvalidInput("invalid UTF-8") from exc

    parents = {identifier: parent for _, identifier, parent in rows}
    line_for = {identifier: line for line, identifier, _ in rows}
    findings: list[dict[str, Any]] = []
    for line, _identifier, parent in rows:
        if parent is not None and parent not in parents:
            findings.append({"line": line, "kind": "missing_parent"})

    # Each unprocessed node follows at most one outgoing edge. Track its current
    # path and positions to identify only cycle members, never incoming tails.
    finished: set[str] = set()
    cycle_ids: set[str] = set()
    for _, start, _ in rows:
        if start in finished:
            continue
        path: list[str] = []
        position: dict[str, int] = {}
        node: str | None = start
        while node is not None and node in parents and node not in finished:
            if node in position:
                cycle_ids.update(path[position[node] :])
                break
            position[node] = len(path)
            path.append(node)
            node = parents[node]
        finished.update(path)

    for identifier in cycle_ids:
        findings.append({"line": line_for[identifier], "kind": "cycle"})
    findings.sort(key=lambda finding: (finding["line"], finding["kind"]))
    roots = sum(parent is None for _, _, parent in rows)
    return {
        "status": "violations" if findings else "valid",
        "record_count": len(rows),
        "root_count": roots,
        "findings": findings,
    }


def validate_text(text: str) -> dict[str, Any]:
    """Convenience API for callers that already hold text."""
    return validate_bytes(text.encode("utf-8"))

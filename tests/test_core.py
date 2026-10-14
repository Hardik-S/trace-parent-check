import json

import pytest

from trace_parent_check.core import InvalidInput, validate_bytes, validate_text


def test_empty_and_multiple_roots_and_out_of_order_parent():
    assert validate_text("") == {
        "status": "valid", "record_count": 0, "root_count": 0, "findings": []
    }
    result = validate_text('{"id":"child","parent":"root"}\n{"id":"root","parent":null}\n{"id":"other","parent":null}')
    assert result == {"status": "valid", "record_count": 3, "root_count": 2, "findings": []}


def test_missing_parents_and_findings_sorted_by_line_then_kind():
    result = validate_text('{"id":"x","parent":"absent"}\n{"id":"a","parent":"b"}\n{"id":"b","parent":"a"}')
    assert result["status"] == "violations"
    assert result["findings"] == [
        {"line": 1, "kind": "missing_parent"},
        {"line": 2, "kind": "cycle"},
        {"line": 3, "kind": "cycle"},
    ]


@pytest.mark.parametrize("text", [
    '{"id":"s","parent":"s"}',
    '{"id":"a","parent":"b"}\n{"id":"b","parent":"c"}\n{"id":"c","parent":"a"}',
])
def test_self_and_multi_node_cycles(text):
    result = validate_text(text)
    assert [finding["kind"] for finding in result["findings"]] == ["cycle"] * result["record_count"]


def test_tails_and_disconnected_components_are_not_cycle_members():
    result = validate_text('\n'.join([
        '{"id":"tail","parent":"a"}',
        '{"id":"a","parent":"b"}',
        '{"id":"b","parent":"a"}',
        '{"id":"isolated","parent":null}',
        '{"id":"missing-tail","parent":"gone"}',
    ]))
    assert result["findings"] == [
        {"line": 2, "kind": "cycle"},
        {"line": 3, "kind": "cycle"},
        {"line": 5, "kind": "missing_parent"},
    ]


def test_long_chain_and_cycle_are_iterative():
    count = 6000
    chain = [json.dumps({"id": f"n{i}", "parent": f"n{i + 1}" if i + 1 < count else None}) for i in range(count)]
    assert validate_text("\n".join(chain))["status"] == "valid"
    chain[-1] = json.dumps({"id": f"n{count - 1}", "parent": "n0"})
    result = validate_text("\n".join(chain))
    assert len(result["findings"]) == count
    assert all(finding["kind"] == "cycle" for finding in result["findings"])


def test_unicode_is_exact_and_crlf_and_cr_are_supported():
    assert validate_bytes('{"id":"é","parent":null}\r{"id":"é","parent":"é"}\r\n'.encode())["status"] == "valid"


@pytest.mark.parametrize("data", [
    b"\xff", b"\n", b'{"id":"a","parent":null}\n\n',
    b'{"id":"a","parent":null}\n{"id":"a","parent":null}',
    b'{"id":"a","parent":null,"extra":1}', b'{"id":"","parent":null}',
    b'{"id":"a","parent":""}', b'{"id":"a","parent":1}',
    b'{"id":"a","parent":null,"id":"b"}', b'{"id":"a","parent":NaN}',
    b'{"id":"a","parent":null}\nnot json',
])
def test_strict_invalid_input(data):
    with pytest.raises(InvalidInput):
        validate_bytes(data)

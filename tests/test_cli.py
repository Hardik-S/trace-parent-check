import json
import subprocess
import sys


def run_cli(path):
    return subprocess.run(
        [sys.executable, "-m", "trace_parent_check.cli", str(path)],
        capture_output=True,
        text=True,
    )


def test_cli_valid_and_violation_codes(tmp_path):
    source = tmp_path / "spans.jsonl"
    source.write_text('{"id":"root","parent":null}\n', encoding="utf-8")
    valid = run_cli(source)
    assert valid.returncode == 0 and not valid.stderr
    assert json.loads(valid.stdout)["status"] == "valid"
    source.write_text('{"id":"child","parent":"secret-span-id"}\n', encoding="utf-8")
    violation = run_cli(source)
    assert violation.returncode == 1 and not violation.stderr
    assert json.loads(violation.stdout)["findings"] == [{"line": 1, "kind": "missing_parent"}]
    assert "secret-span-id" not in violation.stdout


def test_cli_invalid_has_exact_safe_output_even_for_valid_prefix(tmp_path):
    source = tmp_path / "spans.jsonl"
    source.write_bytes(b'{"id":"safe","parent":null}\n{"id":"sensitive","parent":[')
    result = run_cli(source)
    assert result.returncode == 2
    assert result.stdout == '{"status":"invalid_input"}\n'
    assert result.stderr == ""
    assert "sensitive" not in result.stdout


def test_missing_file_is_safe_invalid_input(tmp_path):
    result = run_cli(tmp_path / "missing.jsonl")
    assert result.returncode == 2
    assert result.stdout == '{"status":"invalid_input"}\n'
    assert result.stderr == ""

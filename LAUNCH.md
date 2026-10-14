# v0.1.0 launch checklist

## Fresh-install quickstart

```console
python -m venv .venv
# Activate .venv
python -m pip install .
trace-parent-check examples/valid.jsonl
```

The command exits 0 and reports `status: valid`. Try `examples/violations.jsonl` for exit 1 and cycle/dangling-parent findings, then `examples/invalid.jsonl` for exit 2 and the safe `invalid_input` response. These fixtures are synthetic.

## Release checks

- Install the package from a clean environment and run all three examples.
- Install `.[test]` and run `python -m pytest`.
- Confirm the GitHub Actions matrix passes on Ubuntu and Windows with Python 3.10 and 3.13.
- Tag the reviewed commit `v0.1.0` only after those checks pass.

This tool validates normalized parent relationships only. It does not establish trace completeness, provider provenance, timing correctness, or runtime safety.

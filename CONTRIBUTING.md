# Contributing

Thanks for helping improve RadScan Lite. Keep contributions small, testable, and free of patient data.

## Development Setup

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Before Opening a Pull Request

Run:

```bash
python -m ruff check radscan_lite tests scripts
python -m mypy radscan_lite
python -m pytest -q --cov=radscan_lite --cov-report=term-missing --cov-fail-under=80
```

## Contribution Rules

- Do not commit PHI, real patient DICOM files, credentials, or private institutional exports.
- Use synthetic DICOM data for tests, screenshots, and examples.
- Add tests for scanner, archive, privacy, reporting, or UI behavior changes.
- Keep privacy and compliance claims conservative.
- Update README or docs when commands, outputs, or assumptions change.

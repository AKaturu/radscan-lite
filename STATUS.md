# RadScan Lite — Project Status

## Current Release

**v0.1.0** — Initial release providing a local, read-only DICOM dataset preflight scanner for radiology researchers.

## Implemented Features

- Core scanner engine: file validity, pixel data integrity, dataset integrity, series consistency, privacy review, archive safety
- Streamlit web UI with upload area, status cards, findings by severity, study/series summaries, privacy warnings, thumbnails, and CSV/JSON download
- Three built-in check profiles: full, structure-only, sharing-review
- Synthetic data generation for three test scenarios (clean, inconsistent, privacy-warning)
- Secure ZIP extraction with path traversal prevention and compression-ratio limits
- CSV and JSON report generation (PHI-free)
- Desktop release packaging via PyInstaller (Windows, macOS, Linux)
- CLI launcher and Docker support

## Quality Gates

- 29 pytest tests passing
- Coverage gate at 80% (enforced in CI)
- No ruff violations
- No mypy errors

## Known Issues

- FrameOfReferenceUID values in synthetic data emit pydicom warnings (invalid UI format for test data only)
- `write_like_original` is deprecated in pydicom 3.x in favor of `enforce_file_format` (no functional impact)
- Test suite generates ~300 MB of temporary DICOM files during session-scoped fixtures
- Optional pylibjpeg dependency noted in docs but not tested

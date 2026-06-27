# PROJECT_STATE

## Project Overview

### Project Name
RadScan Lite — DICOM Dataset Preflight Scanner

### Goal
A local, read-only DICOM dataset scanner for radiology researchers that inspects files for structural problems, series inconsistencies, duplicate identifiers, pixel decoding failures, and potential privacy risks.

### Current Status
Phase 10 (configurable check profiles) - Complete. Core scanner remains validated, repository presentation has been refreshed, and the dashboard now supports context-specific report profiles.

---

## Completed Features

### Feature: Core Scanner Engine
#### Validation
All 29 pytest tests pass. The scanner correctly handles valid DICOM, malformed files, missing UIDs, corrupt pixel data, inconsistent series dimensions, duplicate instance numbers, PHI tag detection, BurnedInAnnotation (YES/NO/missing), private tags, and multi-frame files.

#### Tests Added
- `test_scanner.py` — 29 tests across 10 test classes covering all modules

### Feature: Streamlit Web UI
#### Validation
`app.py` provides upload area, status cards, findings by severity, study/series summaries, invalid-files table, privacy warnings, thumbnails, CSV/JSON download, and disclaimer.

### Feature: Synthetic Data Generation
#### Validation
`scripts/generate_synthetic_data.py` generates three series: clean (5 CT files), inconsistent (5 files with varying dimensions, spacing, orientation), and privacy-warning (5 files with PHI fields).

### Feature: Secure ZIP Extraction
#### Validation
Archive security tests pass: normal extraction, empty ZIP, compression ratio limit rejection, and temp directory cleanup.

### Feature: Reporting
#### Validation
CSV and JSON reports generate correctly. PHI values are confirmed absent from all reports.

### Feature: Coverage Reporting Gate
#### Validation
The development dependency set now includes `pytest-cov`, CI runs coverage-gated tests on Python 3.11 and 3.12, and README/CONTRIBUTING commands match the enforced coverage gate.

#### Tests Added
No new scanner tests were needed; this roadmap item strengthens test reporting and CI enforcement.

### Feature: Desktop Release Packaging
#### Validation
Local PyInstaller scripts now run from the repository root or from CI, the frozen launcher uses Streamlit directly instead of shelling out to a Python interpreter, and GitHub Actions can build Windows ZIP, macOS DMG, and Linux tar.gz artifacts.

#### Tests Added
Release workflow includes packaged launcher `--self-check` smoke tests.

### Feature: Configurable Check Profiles
#### Validation
The scanner now supports built-in `full`, `structure-only`, and `sharing-review` profiles. Profiles are applied as a report overlay so raw scanning remains read-only and unchanged; the dashboard exposes the profile selector before scanning, JSON reports record the active profile, and reports respect suppressed privacy rules or severity overrides.

#### Tests Added
- `TestScanProfiles` verifies that `structure-only` suppresses `PRIV-*` findings from CSV/JSON reports and that `sharing-review` raises private-tag findings to warning severity.

---

## Current Work

### Active Feature
N/A — All features complete.

### Progress
100%. README, contribution/security docs, package metadata, CI branch targeting, coverage reporting, desktop release packaging, and configurable check profiles have been refreshed for the public GitHub repository.

### Remaining Work
None

---

## Next Actions

1. Run `streamlit run app.py` to manually verify the UI before tagged releases.
2. Cut a version tag such as `v0.1.0` to trigger the desktop release workflow and attach artifacts to a GitHub Release.
3. Publish to PyPI when release artifacts are ready.
4. Keep coverage reporting above the CI floor as the scanner grows.
5. Consider a future custom profile file format if users need site-specific rule overrides beyond the built-in profiles.

---

## Risks

### Open Questions
None

### Known Issues
- FrameOfReferenceUID values in synthetic data emit pydicom warnings (invalid UI format for test data only)
- `write_like_original` is deprecated in pydicom 3.x in favor of `enforce_file_format` (no functional impact)

### Technical Concerns
- Test suite generates ~300MB of temporary DICOM files during session-scoped fixtures
- Optional pylibjpeg dependency noted in docs but not tested

---

## Resume Instructions

Start here: `app.py` is the Streamlit entry point. The core logic lives in `radscan_lite/`. Run `python -m ruff check radscan_lite tests scripts`, `python -m mypy radscan_lite`, and `python -m pytest -q` to verify the repository. Run `streamlit run app.py` to launch the UI. The synthetic data generation script is at `scripts/generate_synthetic_data.py`. Desktop release details are in `docs/DESKTOP_RELEASES.md`.

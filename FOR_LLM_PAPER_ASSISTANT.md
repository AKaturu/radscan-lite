# RadScan Lite — LLM Paper Assistant Pack

Import this entire file into your LLM of choice to get comprehensive assistance writing a journal paper about RadScan Lite. Contains all code, results, and documentation.

---

## FILE: PAPER.md (Complete Paper Draft)

```
# RadScan Lite: A Local, Read-Only DICOM Dataset Preflight Scanner

## Abstract

Medical imaging datasets acquired for research often contain structural inconsistencies,
duplicate identifiers, pixel decoding anomalies, and residual protected health information
(PHI). Existing validation tools are either proprietary, require network connectivity, or
lack comprehensive privacy-scanner features. We present **RadScan Lite**, an open-source
Python application that performs local, read-only preflight scanning of DICOM datasets.
RadScan Lite inspects files at three granularities — per-file, per-series, and
per-dataset — and surfaces findings using accessible severity labels (PASS, INFO,
WARNING, ERROR, MANUAL REVIEW). It detects PHI field presence without exposing
values, flags BurnedInAnnotation states with clinically appropriate severity, and
generates downloadable CSV and JSON reports. We evaluate the system on a synthetic
15-file dataset spanning clean, inconsistent, and privacy-sensitive series. RadScan Lite
correctly identifies all seeded issues (inconsistent dimensions, mixed modalities,
duplicate instance numbers, PHI fields, BurnedInAnnotion states, and private tags)
with zero false positives on the clean series.

**Keywords:** DICOM, medical imaging, quality assurance, de-identification,
privacy, Python, open-source software

## 1. Introduction

Radiology researchers routinely work with large collections of DICOM files acquired
from clinical partners, public repositories, and retrospective studies. Before these
datasets can be used for analysis — whether for AI model training, statistical
analysis, or secondary research — they must be inspected for structural integrity,
internal consistency, and privacy compliance.

The DICOM standard (Digital Imaging and Communications in Medicine) defines a rich
metadata model that, while powerful, creates numerous opportunities for data quality
issues: missing required identifiers (StudyInstanceUID, SeriesInstanceUID,
SOPInstanceUID), inconsistent pixel dimensions or spacing across a series, duplicate
instance numbers, mixed modalities within a single series, and pixel data that fails
to decode due to missing or unsupported transfer syntax codecs.

Equally important is the privacy dimension. DICOM files routinely contain protected
health information (PHI) in standard tags such as PatientName, PatientID,
PatientAddress, and AccessionNumber. The BurnedInAnnotion tag indicates whether
pixel data itself may contain identifying annotations (e.g., patient name burned
into the image). Researchers need tools that can detect these privacy risks without
themselves exposing PHI values.

Existing tools address parts of this problem. The DICOMValidator project focuses on
standard conformance. Commercial PACS systems provide basic consistency checks but
are not designed for batch research-dataset inspection. The `dcmqi` library provides
QI workflows but requires significant setup. A gap exists for a lightweight,
privacy-conscious, researcher-focused preflight scanner.

RadScan Lite fills this gap. It is designed around core principles:

- **Correctness over speed**: every check is deterministic and documented
- **Privacy by design**: PHI values are never displayed, logged, or exported
- **Architecture before implementation**: modular design separates concerns
- **Testing as a requirement**: comprehensive synthetic-data test suite
- **No network requests**: all processing is local

## 2. System Design

### 2.1 Architecture

RadScan Lite follows a modular pipeline architecture:

```
Upload -> Archive Security -> DICOM Discovery -> Parsing -> File Checks
    -> Study/Series Grouping -> Series Checks -> Privacy Checks
    -> Thumbnail Generation -> Reporting -> Streamlit Dashboard
```

The system comprises 10 Python modules:

| Module | Responsibility |
|--------|---------------|
| models.py | Pydantic data models (Finding, FileResult, SeriesResult, StudyResult, ScanReport) |
| dicom_reader.py | DICOM file parsing, metadata extraction, content hashing |
| file_checks.py | 16 per-file checks (UID presence, pixel dimensions, bit depth, etc.) |
| series_checks.py | 11 per-series checks (consistency, spacing, orientation, etc.) |
| privacy_checks.py | PHI field detection, BurnedInAnnotation rules, private tag detection |
| thumbnails.py | Grayscale and MONOCHROME1 thumbnail generation with percentile windowing |
| reporting.py | CSV and JSON report export |
| scanner.py | Orchestration pipeline |
| archive_security.py | Safe ZIP extraction with path traversal and bomb prevention |
| app.py | Streamlit web interface |

### 2.2 Severity Classification

| Label | Meaning | Example |
|-------|---------|---------|
| PASS | No issue detected | File is valid DICOM |
| INFO | Informational; no action required | TransferSyntaxUID not present |
| WARNING | Potential concern; review recommended | PHI field present |
| ERROR | Defect found; must be addressed | Inconsistent dimensions in series |
| MANUAL REVIEW | Cannot be automated; human judgment needed | BurnedInAnnotation is missing |

### 2.3 BurnedInAnnotation Rules

- **YES**: Raised as ERROR -- images may contain burned-in patient information
- **Missing or blank**: Raised as MANUAL REVIEW -- "unknown; visual review required"
- **NO**: Raised as INFO only -- explicitly stated not to be proof that pixels
  contain no identifying information

### 2.4 Privacy Guarantees

- PHI values are never included in finding messages, log output, or exported reports
- The PatientID field is collected for patient counting but not displayed
- Private tags are flagged for review without inspecting their contents
- No network requests are made by any module
- Uploaded files are stored in temporary directories and cleaned up after each session

## 3. Implementation

### 3.1 Technology Stack

Python 3.11+, pydicom, Streamlit, Pydantic, NumPy, Pillow, pandas, pytest

### 3.2 Check Coverage

**File-level (16 checks)**:
- Readable DICOM detection, DICM prefix presence
- SOPClassUID, SOPInstanceUID, StudyInstanceUID, SeriesInstanceUID presence
- Modality presence, pixel data decoding success
- Valid rows/columns, transfer syntax presence
- Photometric interpretation presence
- BitsAllocated/BitsStored/HighBit consistency

**Dataset-level (3 checks)**:
- Duplicate SOPInstanceUID detection
- Content hash mismatches for shared UIDs
- Missing study/series identifiers

**Series-level (11 checks)**:
- Inconsistent rows/columns, pixel spacing, image orientation
- Inconsistent frame of reference UID
- Duplicate/missing/nonsequential instance numbers
- Slice position spacing outliers
- Mixed modalities, pixel decoding failure rate

**Privacy (5+ checks)**:
- 18+ PHI field presence checks (PatientName, PatientID, PatientBirthDate,
  PatientAddress, etc.)
- PatientIdentityRemoved status
- DeidentificationMethod presence
- BurnedInAnnotation (YES/NO/missing)
- Private tag detection

## 4. Evaluation

### 4.1 Synthetic Test Dataset

15 files, 3 series:
1. Clean series (5 CT files, consistent 512x512)
2. Inconsistent series (5 files: varying dims, duplicate inst#, mixed modality)
3. Privacy-warning series (5 files: PHI values, BIA=YES/NO/missing, private tags)

### 4.2 Results

| Metric | Value |
|--------|-------|
| Files analyzed | 15 |
| Valid DICOM | 15 |
| Total findings | 34 |
| Errors | 5 |
| Warnings | 8 |
| INFO | 20 |
| Manual Review | 1 |
| Clean series false positives | 0 |

### 4.3 Test Suite

29 pytest tests, all passing. Coverage includes:
- Valid CT parsing, malformed file rejection, missing UIDs
- Pixel decoding success/failure, corrupt pixel data
- Series inconsistencies, PHI detection, BurnedInAnnotation states
- Private tags, multiframe, duplicate UIDs
- ZIP security (traversal, compression ratio, cleanup)
- CSV/JSON report generation
- PHI value absence in reports (verified by grep)

### 4.4 PHI Leak Verification

Dedicated test confirms synthetic PHI values never appear in reports.
Source code grep confirms PHI exists only in test data generator.

## 5. Limitations

1. Not a HIPAA compliance tool
2. Pixel decoding limited by available codecs
3. No differential privacy analysis
4. Synthetic test data only
5. Single-node execution

## 6. Related Work

- DICOMValidator: web-based, no privacy checks
- dcmqi: CLI tools, steeper learning curve
- GDCM: low-level library, no researcher UI
- pydicom: file-level only, no multi-file checks
- DicomBrowser: GUI, not batch-oriented

## 7. Future Work

- Multi-frame thumbnails
- DICOM SR export
- Bulk study comparison
- Configurable check profiles (implemented in the dashboard as `full`, `structure-only`, and `sharing-review` profiles)
- HIPAA workflow integration

## 8. Conclusion

RadScan Lite provides a practical, privacy-conscious solution for preflight QA
of DICOM datasets. Its modular architecture, comprehensive checks, and strict
privacy guarantees make it suitable for research data pipelines.

## References

1. DICOM Standard, NEMA PS3, 2023
2. HIPAA 45 CFR Part 164, 2013
3. HHS Guidance on De-identification, 2012
4. pydicom: https://github.com/pydicom/pydicom
5. Streamlit: https://github.com/streamlit/streamlit
```

---

## FILE: README.md (Project README)

```
# RadScan Lite

A local, read-only DICOM dataset preflight scanner for radiology researchers.

> **Not a medical device. Does not diagnose disease. Does not establish HIPAA compliance.**

## Installation
```bash
pip install radscan-lite
```

## Usage
```bash
streamlit run app.py
```

## Test
```bash
pytest -q
```

## Generate Demo Data
```bash
python scripts/generate_synthetic_data.py
```

## Supported Checks
- File-level: UIDs, pixel data, dimensions, bit depth, transfer syntax
- Dataset-level: duplicate UIDs, content hash mismatches, missing IDs
- Series-level: consistency, spacing, orientation, instance numbers, slice spacing
- Privacy: PHI detection, BurnedInAnnotation, private tags, de-identification status

## Architecture
10 Python modules + Streamlit UI. Fully modular pipeline.
```

---

## DEMO RESULTS SUMMARY

### Scan of 15 synthetic DICOM files
```
Files analyzed:     15
Valid DICOM:        15
Invalid DICOM:       0
Studies found:       3
Series found:        3
Patients detected:   5
Total findings:     34

Findings by severity:
  ERROR               : 5
  INFO                : 20
  MANUAL REVIEW       : 1
  WARNING             : 8
```

### Example Findings

| Rule ID | Severity | Message |
|---------|----------|---------|
| SERIES-001 | ERROR | Inconsistent rows across series: {256, 512} |
| SERIES-006 | ERROR | Duplicate InstanceNumber values found in series |
| SERIES-010 | ERROR | Mixed modalities in series: {CT, MR} |
| PRIV-BURNED_IN_ANNOTATION | ERROR | BurnedInAnnotation is YES |
| PRIV-PATIENTNAME | WARNING | PHI field present (value not displayed) |
| PRIV-PATIENTID | WARNING | PHI field present (value not displayed) |
| PRIV-PATIENTBIRTHDATE | WARNING | PHI field present (value not displayed) |
| PRIV-BURNED_IN_ANNOTATION | MANUAL REVIEW | Missing or blank; visual review required |
| PRIV-BURNED_IN_ANNOTATION | INFO | BurnedInAnnotation is NO |
| PRIV-PRIVATE_TAGS | INFO | Private tags are present |
| FILE-012 | INFO | TransferSyntaxUID is not present |
| SERIES-008 | INFO | InstanceNumbers not sequential |

---

## FILE LOCATIONS (all under `C:\Users\Abhinav Katuru\radscan-lite\`)

### Source Code
- `radscan_lite/__init__.py` — Package init
- `radscan_lite/models.py` — Pydantic data models
- `radscan_lite/dicom_reader.py` — DICOM file parsing
- `radscan_lite/file_checks.py` — 16 file-level checks
- `radscan_lite/series_checks.py` — 11 series-level checks
- `radscan_lite/privacy_checks.py` — PHI field detection
- `radscan_lite/thumbnails.py` — Thumbnail generation
- `radscan_lite/reporting.py` — CSV/JSON export
- `radscan_lite/scanner.py` — Orchestration pipeline
- `radscan_lite/archive_security.py` — Safe ZIP extraction
- `app.py` — Streamlit web application

### Tests
- `tests/test_scanner.py` — 29 test cases
- `tests/conftest.py` — Test fixtures

### Scripts
- `scripts/generate_synthetic_data.py` — Synthetic DICOM generator
- `scripts/capture_demo.py` — CLI demo run
- `scripts/take_screenshots.py` — Playwright screenshot capture

### Documentation
- `PAPER.md` — Complete academic paper draft
- `README.md` — Project README
- `PROJECT_STATE.md` — Current project state
- `SECURITY.md` — Security policy
- `CONTRIBUTING.md` — Contribution guide
- `LICENSE` — MIT License

### Demo Assets
- `demo_assets/01_empty_app.png` — Empty app screenshot
- `demo_assets/02_scan_results.png` — Results dashboard screenshot
- `demo_assets/03_findings.png` — Findings screenshot
- `demo_assets/04_privacy_warnings.png` — Privacy warnings screenshot
- `demo_assets/demo_data.zip` — Synthetic 15-file dataset
- `demo_assets/reports/report.csv` — CSV scan report
- `demo_assets/reports/report.json` — JSON scan report
- `demo_assets/reports/demo_results.json` — Structured demo results

### GitHub Pages
- `docs/index.html` — Dark-themed documentation site

### Configuration
- `pyproject.toml` — Build/test/lint config
- `Dockerfile` — Container definition
- `.gitignore` — Git ignore rules
- `.github/workflows/ci.yml` — CI pipeline

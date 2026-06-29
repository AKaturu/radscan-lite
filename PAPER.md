# RadScan Lite: A Local, Read-Only DICOM Dataset Preflight Scanner

**Draft manuscript - not peer reviewed and not submitted. Results are derived from synthetic
test data unless otherwise stated.**

## Abstract

Medical imaging datasets acquired for research often contain structural inconsistencies,
duplicate identifiers, pixel decoding anomalies, and residual protected health information
(PHI). Existing validation tools are either proprietary, require network connectivity, or
do not provide the same lightweight local preflight workflow. We present **RadScan Lite**, an open-source
Python application that performs local, read-only preflight scanning of DICOM datasets.
RadScan Lite inspects files at three granularities — per-file, per-series, and
per-dataset — and surfaces findings using accessible severity labels (PASS, INFO,
WARNING, ERROR, MANUAL REVIEW). It detects PHI field presence without exposing
values, flags BurnedInAnnotation states with clinically appropriate severity, and
generates downloadable CSV and JSON reports. We evaluate the system on a synthetic
15-file dataset spanning clean, inconsistent, and privacy-sensitive series. RadScan Lite
detected the seeded synthetic issues in this dataset, including inconsistent dimensions,
mixed modalities, duplicate instance numbers, PHI fields, BurnedInAnnotion states, and
private tags, and did not flag the clean synthetic series.

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
- **Testing as a requirement**: focused synthetic-data test suite
- **No network requests**: all processing is local

## 2. System Design

### 2.1 Architecture

RadScan Lite follows a modular pipeline architecture:

```
Upload → Archive Security → DICOM Discovery → Parsing → File Checks
    → Study/Series Grouping → Series Checks → Privacy Checks
    → Thumbnail Generation → Reporting → Streamlit Dashboard
```

The system comprises 10 Python modules:

| Module | Responsibility |
|--------|---------------|
| `models.py` | Pydantic data models (Finding, FileResult, SeriesResult, StudyResult, ScanReport) |
| `dicom_reader.py` | DICOM file parsing, metadata extraction, content hashing |
| `file_checks.py` | 16 per-file checks (UID presence, pixel dimensions, bit depth, etc.) |
| `series_checks.py` | 11 per-series checks (consistency, spacing, orientation, etc.) |
| `privacy_checks.py` | PHI field detection, BurnedInAnnotation rules, private tag detection |
| `thumbnails.py` | Grayscale and MONOCHROME1 thumbnail generation with percentile windowing |
| `reporting.py` | CSV and JSON report export |
| `scanner.py` | Orchestration pipeline |
| `archive_security.py` | Safe ZIP extraction with path traversal and bomb prevention |
| `app.py` | Streamlit web interface |

### 2.2 Severity Classification

Findings use five severity levels, designed to be accessible without color-only
discrimination:

| Label | Meaning | Example |
|-------|---------|---------|
| PASS | No issue detected | File is valid DICOM |
| INFO | Informational; no action required | TransferSyntaxUID not present |
| WARNING | Potential concern; review recommended | PHI field present |
| ERROR | Defect found; must be addressed | Inconsistent dimensions in series |
| MANUAL REVIEW | Cannot be automated; human judgment needed | BurnedInAnnotation is missing |

### 2.3 BurnedInAnnotation Rules

The BurnedInAnnotion tag receives special handling in accordance with DICOM
standard and HIPAASafe Harbor guidance:

- **YES**: Raised as ERROR — images may contain burned-in patient information
- **Missing or blank**: Raised as MANUAL REVIEW — "unknown; visual review required"
- **NO**: Raised as INFO only — explicitly stated not to be proof that pixels
  contain no identifying information

### 2.4 Privacy Guarantees

RadScan Lite implements strict privacy protections:

- PHI values are never included in finding messages, log output, or exported reports
- The `PatientID` field is collected for patient counting but not displayed
- Private tags are flagged for review without inspecting their contents
- No network requests are made by any module
- Uploaded files are stored in temporary directories and cleaned up after each session

## 3. Implementation

### 3.1 Technology Stack

RadScan Lite is written in Python 3.11+ and uses:

- **pydicom** for DICOM file parsing and metadata extraction
- **Streamlit** for the web interface
- **Pydantic** for type-safe data models with JSON serialization
- **NumPy** for pixel array manipulation
- **Pillow** for thumbnail generation
- **pandas** for data presentation (optional, used in Streamlit)
- **pytest** for the test suite

### 3.2 Package Structure

```
radscan_lite/
  __init__.py
  models.py          — Data models
  scanner.py         — Orchestrator
  dicom_reader.py    — DICOM parsing
  file_checks.py     — File-level checks
  series_checks.py   — Series-level checks
  privacy_checks.py  — Privacy checks
  thumbnails.py      — Thumbnail generation
  reporting.py       — Report export
  archive_security.py — Safe ZIP handling
app.py               — Streamlit entry point
tests/
  test_scanner.py    — 29 test cases
scripts/
  generate_synthetic_data.py — Test data generator
```

### 3.3 Check Coverage

The scanner implements 30+ individual checks across four scopes:

**File-level (16 checks)**: readable DICOM detection, DICM prefix presence,
SOPClassUID presence, SOPInstanceUID presence, StudyInstanceUID presence,
SeriesInstanceUID presence, Modality presence, pixel data decoding success,
pixel data presence when expected, valid rows, valid columns, transfer syntax
presence, photometric interpretation presence, BitsAllocated/BitsStored/HighBit
consistency, HighBit vs BitsStored consistency.

**Dataset-level (3 checks)**: duplicate SOPInstanceUID detection, content hash
mismatches for shared UIDs, missing study/series identifiers.

**Series-level (11 checks)**: inconsistent rows, inconsistent columns,
inconsistent pixel spacing, inconsistent image orientation, inconsistent frame
of reference UID, duplicate instance numbers, missing instance numbers,
nonsequential instance numbers, slice position spacing outliers, mixed
modalities, pixel decoding failure rate.

**Privacy (5+ checks)**: 18+ PHI field presence checks, PatientIdentityRemoved
status, DeidentificationMethod presence, BurnedInAnnotation (YES/NO/missing),
private tag detection.

## 4. Evaluation

### 4.1 Synthetic Test Dataset

We created a synthetic DICOM dataset containing 15 files across three series:

1. **Clean series** (5 files): Valid CT images with consistent dimensions (512x512),
   sequential instance numbers, uniform pixel spacing, consistent orientation, and
   no PHI fields.
2. **Inconsistent series** (5 files): Deliberately seeded with inconsistent dimensions
   (alternating 256x256 and 512x512), a duplicate instance number, mixed pixel spacing,
   mixed orientation, and a modality change (CT to MR).
3. **Privacy-warning series** (5 files): Seeded with PHI values (PatientName,
   PatientID, PatientBirthDate, PatientAddress), BurnedInAnnotation=YES,
   BurnedInAnnotation=NO, BurnedInAnnotation=missing, and private tags.

### 4.2 Results

The scanner analyzed all 15 files and produced 34 findings:

| Severity | Count | Examples |
|----------|-------|---------|
| ERROR | 5 | Inconsistent dimensions, duplicate instance numbers, mixed modalities, BurnedInAnnotation=YES |
| WARNING | 8 | PHI field presence, inconsistent pixel spacing, inconsistent orientation |
| INFO | 20 | TransferSyntaxUID missing, DeidentificationMethod missing, PatientIdentityRemoved missing, BurnedInAnnotation=NO, private tags present |
| MANUAL REVIEW | 1 | BurnedInAnnotation missing |

The clean synthetic series produced zero findings in this benchmark.

### 4.3 Test Suite

The test suite comprises 29 pytest test cases covering:

- Valid DICOM parsing (CT file with all required fields)
- Malformed file rejection
- Missing UID detection
- DICM prefix validation
- Pixel data decoding (success and failure)
- Series-level inconsistency detection (dimensions, pixel spacing, instance numbers)
- PHI tag presence (PatientName, PatientID, BurnedInAnnotation states)
- Private tag detection
- PHI value absence in reports
- MONOCHROME1 thumbnail generation
- Multiframe support
- Duplicate SOPInstanceUID detection
- ZIP extraction security (normal, empty, traversal prevention, compression ratio)
- CSV and JSON report generation

All 29 tests pass on Python 3.12.

### 4.4 PHI Leak Verification

A dedicated test (test_phi_values_not_in_reports) confirms that synthetic PHI
values (DOE^JOHN, SMITH^JANE, ID123456, 19700101, 123 Main St) never appear in
CSV or JSON report output. Grep verification of the entire source code confirms
these values exist only in the synthetic data generator and the PHI-leak test
itself.

## 5. Limitations

1. **Not a HIPAA compliance tool**: RadScan Lite cannot guarantee full
   de-identification. It flags known PHI fields but cannot detect PHI in
   non-standard tags, private tags without creators, or burned-in annotations
   when BurnedInAnnotation is NO.
2. **Pixel decoding limited by codecs**: Support for JPEG-LS, JPEG-2000, and
   other compressed transfer syntaxes requires optional `pylibjpeg` dependencies.
3. **No differential privacy analysis**: The scanner does not assess whether
   de-identification is sufficient to prevent re-identification.
4. **Synthetic test data only**: Evaluation was performed on synthetic data;
   validation on real clinical datasets is needed.
5. **Single-node**: The application runs on a single machine and does not
   support distributed scanning.

## 6. Related Work

- **DICOMValidator** (dicomvalidator.com): Web-based DICOM validation against
  IHE profiles. Requires network connectivity and does not perform privacy checks.
- **dcmqi** (github.com/QIICR/dcmqi): Command-line DICOM conversion and
  validation tools. More comprehensive but has a steeper learning curve.
- **GDCM** (github.com/malaterre/GDCM): Low-level DICOM library with validation
  capabilities. Lacks a researcher-oriented interface.
- **pydicom** (github.com/pydicom/pydicom): The underlying library used by
  RadScan Lite. Provides file-level validation but no multi-file or privacy checks.
- **DicomBrowser**: GUI tool for DICOM exploration. Not designed for batch
  preflight scanning.

RadScan Lite is intended to be useful through its combination of multi-file consistency
checking, privacy-aware design, automated severity classification, and
researcher-friendly Streamlit interface.

## 7. Future Work

- Multi-frame thumbnail support for volumetric series
- Structured report export (DICOM SR)
- Bulk study comparison across multiple datasets
- Configurable check profiles for different research contexts (implemented in the dashboard as `full`, `structure-only`, and `sharing-review` profiles)
- Integration with HIPAA Safe Harbor and Expert Determination workflows

## 8. Conclusion

RadScan Lite provides a practical, privacy-conscious solution for preflight
quality assurance of DICOM datasets in research settings. Its modular
architecture, documented check coverage, and privacy safeguards
make it suitable for integration into research data pipelines. The tool is
open-source and available at https://github.com/AKaturu/radscan-lite.

## Acknowledgments

This project was developed as an open-source research tool. No external funding
was received. The authors thank the pydicom and Streamlit communities for their
excellent libraries.

## References

1. Digital Imaging and Communications in Medicine (DICOM) Standard, NEMA PS3,
   National Electrical Manufacturers Association, 2023.
2. HIPAA Administrative Simplification Regulation Text, 45 CFR Part 164,
   U.S. Department of Health and Human Services, 2013.
3. Office for Civil Rights, "Guidance Regarding Methods for De-identification
   of Protected Health Information," U.S. Department of Health and Human
   Services, 2012.
4. pydicom contributors, "pydicom: A Python library for working with DICOM
   medical imaging files," GitHub, 2024. [Online]. Available:
   https://github.com/pydicom/pydicom
5. Streamlit contributors, "Streamlit: The fastest way to build and share
   data apps," GitHub, 2024. [Online]. Available: https://github.com/streamlit/streamlit

# RadScan Lite

A local, read-only DICOM dataset preflight scanner for radiology researchers. Inspects DICOM files for structural problems, series inconsistencies, duplicate identifiers, pixel decoding failures, and potential privacy risks.

> **Not a medical device. Does not diagnose disease. Does not establish HIPAA compliance.**

## Screenshot

*(Insert screenshot here)*

## Installation

```bash
pip install radscan-lite
```

For development:

```bash
git clone <repo-url>
cd radscan-lite
pip install -e ".[dev]"
```

Optional JPEG-LS / JPEG-2000 support:

```bash
pip install "radscan-lite[pylibjpeg]"
```

## Local Execution

```bash
streamlit run app.py
```

## Test Commands

```bash
pytest -q
pytest -q --cov=radscan_lite  # with coverage
```

## Supported Checks

**File-level:**
- Readable DICOM validation
- DICM prefix detection
- Required UID presence (SOP, Study, Series)
- Modality, pixel data, dimensions, bit depth consistency
- Transfer syntax and photometric interpretation

**Dataset-level:**
- Duplicate SOP Instance UIDs
- Content hash mismatches for same UID
- Missing identifiers

**Series-level:**
- Inconsistent rows/columns, pixel spacing, orientation
- Frame of Reference UID consistency
- Duplicate/missing/non-sequential instance numbers
- Slice spacing outliers
- Mixed modalities
- Pixel decoding failure rate

**Privacy:**
- PHI field presence detection (values never displayed)
- PatientIdentityRemoved and DeidentificationMethod checks
- BurnedInAnnotation (YES=Error, missing/blank=Manual Review, NO=Info only)
- Private tag detection

## Limitations

- Does not diagnose disease
- Does not modify DICOM files
- Not a HIPAA compliance tool
- Cannot guarantee full de-identification
- Pixel decoding depends on available transfer syntax support
- Thumbnails for technical review only

## Privacy & Security

- All processing is local; no data is transmitted or persisted
- PHI values are never displayed, logged, or exported
- ZIP bombs and path traversal attacks are prevented
- Temporary directories are cleaned after each session

## Roadmap

- [ ] Multi-frame thumbnail support
- [ ] Enhanced JPEG-2000 decoding
- [ ] Structured report export (DICOM SR)
- [ ] Bulk study comparison
- [ ] Configurable check profiles

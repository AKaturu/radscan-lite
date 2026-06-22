from __future__ import annotations

from radscan_lite.dicom_reader import has_dicm_prefix
from radscan_lite.models import FileResult, Finding, Scope, Severity


def run_file_checks(file_result: FileResult) -> list[Finding]:
    findings: list[Finding] = []

    _check_readable_dicom(file_result, findings)
    _check_dicm_prefix(file_result, findings)
    _check_required_uids(file_result, findings)
    _check_modality(file_result, findings)
    _check_pixel_data(file_result, findings)
    _check_pixel_dimensions(file_result, findings)
    _check_transfer_syntax(file_result, findings)
    _check_photometric_interpretation(file_result, findings)
    _check_bit_depth(file_result, findings)

    return findings


def _check_readable_dicom(result: FileResult, findings: list[Finding]) -> None:
    if not result.is_valid_dicom:
        findings.append(
            Finding(
                rule_id="FILE-001",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message=f"File is not a readable DICOM file",
                remediation="Verify the file is a valid DICOM Part 10 file or raw DICOM dataset",
                affected_file_count=1,
            )
        )


def _check_dicm_prefix(result: FileResult, findings: list[Finding]) -> None:
    if result.is_valid_dicom:
        has_prefix = has_dicm_prefix(result.path)
        if not has_prefix:
            findings.append(
                Finding(
                    rule_id="FILE-002",
                    severity=Severity.INFO,
                    scope=Scope.FILE,
                    message=f"File does not have DICM prefix (may be a non-Part-10 DICOM file)",
                    remediation="Consider converting to standard Part 10 format for broader compatibility",
                    affected_file_count=1,
                )
            )


def _check_required_uids(result: FileResult, findings: list[Finding]) -> None:
    if not result.is_valid_dicom:
        return

    if result.sop_class_uid is None:
        findings.append(
            Finding(
                rule_id="FILE-003",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message="SOPClassUID is missing",
                remediation="Add SOPClassUID (0008,0016) to the DICOM header",
                affected_file_count=1,
            )
        )
    if result.sop_instance_uid is None:
        findings.append(
            Finding(
                rule_id="FILE-004",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message="SOPInstanceUID is missing",
                remediation="Add SOPInstanceUID (0008,0018) to the DICOM header",
                affected_file_count=1,
            )
        )
    if result.study_instance_uid is None:
        findings.append(
            Finding(
                rule_id="FILE-005",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message="StudyInstanceUID is missing",
                remediation="Add StudyInstanceUID (0020,000D) to the DICOM header",
                affected_file_count=1,
            )
        )
    if result.series_instance_uid is None:
        findings.append(
            Finding(
                rule_id="FILE-006",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message="SeriesInstanceUID is missing",
                remediation="Add SeriesInstanceUID (0020,000E) to the DICOM header",
                affected_file_count=1,
            )
        )


def _check_modality(result: FileResult, findings: list[Finding]) -> None:
    if not result.is_valid_dicom:
        return
    if result.modality is None:
        findings.append(
            Finding(
                rule_id="FILE-007",
                severity=Severity.WARNING,
                scope=Scope.FILE,
                message="Modality is missing",
                remediation="Add Modality (0008,0060) to the DICOM header",
                affected_file_count=1,
            )
        )


def _check_pixel_data(result: FileResult, findings: list[Finding]) -> None:
    if not result.is_valid_dicom:
        return

    has_rows = result.rows is not None
    has_columns = result.columns is not None
    pixel_data_expected = has_rows or has_columns

    if pixel_data_expected:
        if result.pixel_decoding_success is False:
            findings.append(
                Finding(
                    rule_id="FILE-008",
                    severity=Severity.ERROR,
                    scope=Scope.FILE,
                    message="Pixel data decoding failed",
                    remediation="The pixel data may be corrupt or encoded with an unsupported transfer syntax",
                    affected_file_count=1,
                )
            )
        elif result.pixel_decoding_success is None:
            findings.append(
                Finding(
                    rule_id="FILE-009",
                    severity=Severity.WARNING,
                    scope=Scope.FILE,
                    message="Pixel data element is missing when rows/columns are present",
                    remediation="Verify the DICOM file contains valid pixel data",
                    affected_file_count=1,
                )
            )


def _check_pixel_dimensions(result: FileResult, findings: list[Finding]) -> None:
    if not result.is_valid_dicom:
        return
    if result.rows is not None and result.rows < 1:
        findings.append(
            Finding(
                rule_id="FILE-010",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message=f"Invalid Rows value: {result.rows}",
                remediation="Rows (0028,0010) must be a positive integer",
                affected_file_count=1,
            )
        )
    if result.columns is not None and result.columns < 1:
        findings.append(
            Finding(
                rule_id="FILE-011",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message=f"Invalid Columns value: {result.columns}",
                remediation="Columns (0028,0011) must be a positive integer",
                affected_file_count=1,
            )
        )


def _check_transfer_syntax(result: FileResult, findings: list[Finding]) -> None:
    if not result.is_valid_dicom:
        return
    if result.transfer_syntax_uid is None:
        findings.append(
            Finding(
                rule_id="FILE-012",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="TransferSyntaxUID is not present in the dataset",
                remediation="The file may use implicit VR; consider explicit transfer syntax for clarity",
                affected_file_count=1,
            )
        )


def _check_photometric_interpretation(
    result: FileResult, findings: list[Finding]
) -> None:
    if not result.is_valid_dicom:
        return
    if result.photometric_interpretation is None:
        findings.append(
            Finding(
                rule_id="FILE-013",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="PhotometricInterpretation is missing",
                remediation="Add PhotometricInterpretation (0028,0004) for proper pixel data interpretation",
                affected_file_count=1,
            )
        )


def _check_bit_depth(result: FileResult, findings: list[Finding]) -> None:
    if not result.is_valid_dicom:
        return
    ba = result.bits_allocated
    bs = result.bits_stored
    hb = result.high_bit

    if ba is None and (bs is not None or hb is not None):
        findings.append(
            Finding(
                rule_id="FILE-014",
                severity=Severity.WARNING,
                scope=Scope.FILE,
                message="BitsAllocated is missing but BitsStored or HighBit is present",
                remediation="Add BitsAllocated (0028,0100) to the DICOM header",
                affected_file_count=1,
            )
        )

    if ba is not None and bs is not None and hb is not None and bs > ba:
        findings.append(
            Finding(
                rule_id="FILE-015",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message=f"BitsStored ({bs}) exceeds BitsAllocated ({ba})",
                remediation="BitsStored (0028,0101) must be <= BitsAllocated (0028,0100)",
                affected_file_count=1,
            )
        )

    if hb is not None and bs is not None and hb != bs - 1:
        findings.append(
            Finding(
                rule_id="FILE-016",
                severity=Severity.WARNING,
                scope=Scope.FILE,
                message=f"HighBit ({hb}) inconsistent with BitsStored ({bs}) — expected {bs - 1}",
                remediation="HighBit (0028,0102) should typically equal BitsStored - 1",
                affected_file_count=1,
            )
        )

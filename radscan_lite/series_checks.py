from __future__ import annotations

from statistics import median, stdev
from typing import Optional

from radscan_lite.models import FileResult, Finding, Scope, Severity


def run_series_checks(series_files: list[FileResult]) -> list[Finding]:
    findings: list[Finding] = []

    if not series_files:
        return findings

    _check_inconsistent_dimensions(series_files, findings)
    _check_inconsistent_pixel_spacing(series_files, findings)
    _check_inconsistent_orientation(series_files, findings)
    _check_inconsistent_frame_of_reference(series_files, findings)
    _check_duplicate_instance_numbers(series_files, findings)
    _check_missing_instance_numbers(series_files, findings)
    _check_nonsequential_instance_numbers(series_files, findings)
    _check_slice_spacing_outliers(series_files, findings)
    _check_mixed_modalities(series_files, findings)
    _check_pixel_decoding_failures(series_files, findings)

    return findings


def _get_valid_vals(
    series_files: list[FileResult], attr: str
) -> list:
    return [getattr(f, attr) for f in series_files if getattr(f, attr) is not None]


def _check_inconsistent_dimensions(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    rows_set = {f.rows for f in series_files if f.rows is not None}
    cols_set = {f.columns for f in series_files if f.columns is not None}
    if len(rows_set) > 1:
        findings.append(
            Finding(
                rule_id="SERIES-001",
                severity=Severity.ERROR,
                scope=Scope.SERIES,
                message=f"Inconsistent rows across series: {rows_set}",
                remediation="All images in a series should have the same number of rows",
                affected_file_count=sum(
                    1 for f in series_files if f.rows is not None
                ),
            )
        )
    if len(cols_set) > 1:
        findings.append(
            Finding(
                rule_id="SERIES-002",
                severity=Severity.ERROR,
                scope=Scope.SERIES,
                message=f"Inconsistent columns across series: {cols_set}",
                remediation="All images in a series should have the same number of columns",
                affected_file_count=sum(
                    1 for f in series_files if f.columns is not None
                ),
            )
        )


def _check_inconsistent_pixel_spacing(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    spacings = _get_valid_vals(series_files, "pixel_spacing")
    if len(set(spacings)) > 1:
        findings.append(
            Finding(
                rule_id="SERIES-003",
                severity=Severity.WARNING,
                scope=Scope.SERIES,
                message="Inconsistent PixelSpacing across series",
                remediation="Verify pixel spacing is consistent across the series",
                affected_file_count=len(spacings),
            )
        )


def _check_inconsistent_orientation(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    orientations = _get_valid_vals(series_files, "image_orientation_patient")
    if len(set(orientations)) > 1:
        findings.append(
            Finding(
                rule_id="SERIES-004",
                severity=Severity.WARNING,
                scope=Scope.SERIES,
                message="Inconsistent ImageOrientationPatient across series",
                remediation="All images in a series should share the same orientation",
                affected_file_count=len(orientations),
            )
        )


def _check_inconsistent_frame_of_reference(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    fors = _get_valid_vals(series_files, "frame_of_reference_uid")
    if len(set(fors)) > 1:
        findings.append(
            Finding(
                rule_id="SERIES-005",
                severity=Severity.WARNING,
                scope=Scope.SERIES,
                message="Inconsistent FrameOfReferenceUID across series",
                remediation="All images in a series should share the same Frame of Reference UID",
                affected_file_count=len(fors),
            )
        )


def _check_duplicate_instance_numbers(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    inst_nums = [
        f.instance_number
        for f in series_files
        if f.instance_number is not None
    ]
    if len(inst_nums) != len(set(inst_nums)):
        findings.append(
            Finding(
                rule_id="SERIES-006",
                severity=Severity.ERROR,
                scope=Scope.SERIES,
                message="Duplicate InstanceNumber values found in series",
                remediation="Each instance in a series must have a unique InstanceNumber",
                affected_file_count=len(inst_nums),
            )
        )


def _check_missing_instance_numbers(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    missing = [f for f in series_files if f.instance_number is None and f.is_valid_dicom]
    if missing:
        findings.append(
            Finding(
                rule_id="SERIES-007",
                severity=Severity.WARNING,
                scope=Scope.SERIES,
                message=f"{len(missing)} file(s) in series are missing InstanceNumber",
                remediation="Add InstanceNumber (0020,0013) to all instances in the series",
                affected_file_count=len(missing),
            )
        )


def _check_nonsequential_instance_numbers(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    inst_nums = sorted(
        [
            f.instance_number
            for f in series_files
            if f.instance_number is not None
        ]
    )
    if len(inst_nums) > 1:
        expected = list(range(inst_nums[0], inst_nums[0] + len(inst_nums)))
        if inst_nums != expected:
            findings.append(
                Finding(
                    rule_id="SERIES-008",
                    severity=Severity.INFO,
                    scope=Scope.SERIES,
                    message="InstanceNumbers are not sequential or do not start from 1",
                    remediation="Consider using sequential InstanceNumber values starting from 1",
                    affected_file_count=len(inst_nums),
                )
            )


def _extract_slice_position(file_result: FileResult) -> Optional[float]:
    ipp = file_result.image_position_patient
    if ipp is None:
        return None
    try:
        parts = ipp.replace("\\", " ").split()
        if len(parts) >= 3:
            return float(parts[2])
    except (ValueError, TypeError):
        pass
    return None


def _check_slice_spacing_outliers(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    positions = []
    for f in series_files:
        pos = _extract_slice_position(f)
        if pos is not None:
            positions.append(pos)

    if len(positions) < 3:
        return

    sorted_pos = sorted(positions)
    gaps = [
        sorted_pos[i + 1] - sorted_pos[i]
        for i in range(len(sorted_pos) - 1)
    ]
    if len(gaps) < 2:
        return

    try:
        med = median(gaps)
        sd = stdev(gaps)
        threshold = 3 * sd
        outliers = [g for g in gaps if abs(g - med) > threshold]
        if outliers:
            findings.append(
                Finding(
                    rule_id="SERIES-009",
                    severity=Severity.WARNING,
                    scope=Scope.SERIES,
                    message=f"Slice spacing outliers detected: {len(outliers)} gap(s) deviate significantly",
                    remediation="Review slice positions — possible missing or misordered slices",
                    affected_file_count=len(series_files),
                )
            )
    except (ValueError, ZeroDivisionError):
        pass


def _check_mixed_modalities(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    modalities = _get_valid_vals(series_files, "modality")
    if len(set(modalities)) > 1:
        findings.append(
            Finding(
                rule_id="SERIES-010",
                severity=Severity.ERROR,
                scope=Scope.SERIES,
                message=f"Mixed modalities in series: {set(modalities)}",
                remediation="A series should contain only one modality",
                affected_file_count=len(modalities),
            )
        )


def _check_pixel_decoding_failures(
    series_files: list[FileResult], findings: list[Finding]
) -> None:
    total = len(series_files)
    failures = sum(
        1 for f in series_files if f.pixel_decoding_success is False
    )
    if failures > 0:
        rate = failures / total * 100 if total > 0 else 0
        findings.append(
            Finding(
                rule_id="SERIES-011",
                severity=Severity.ERROR,
                scope=Scope.SERIES,
                message=f"Pixel decoding failure rate: {failures}/{total} ({rate:.1f}%)",
                remediation="Check transfer syntax and pixel data encoding",
                affected_file_count=failures,
            )
        )

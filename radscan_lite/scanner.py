from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from radscan_lite.dicom_reader import read_file_result
from radscan_lite.file_checks import run_file_checks
from radscan_lite.models import (
    FileResult,
    Finding,
    ScanReport,
    Scope,
    SeriesResult,
    Severity,
    StudyResult,
)
from radscan_lite.privacy_checks import run_privacy_checks
from radscan_lite.profiles import ScanProfile, apply_scan_profile
from radscan_lite.series_checks import run_series_checks


def scan_directory(
    directory: str | Path,
    profile: str | ScanProfile | None = None,
) -> ScanReport:
    scan_dir = Path(directory)

    candidates = list(_discover_candidates(scan_dir))
    file_results: list[FileResult] = []
    invalid_files: list[FileResult] = []

    for fp in candidates:
        result = read_file_result(fp)
        if result.is_valid_dicom:
            file_results.append(result)
        else:
            invalid_files.append(result)

    for result in file_results:
        result.findings = run_file_checks(result)

    for result in invalid_files:
        result.findings = run_file_checks(result)

    studies: dict[str, list[FileResult]] = defaultdict(list)
    for result in file_results:
        uid = result.study_instance_uid or "MISSING_STUDY_UID"
        studies[uid].append(result)

    study_results: list[StudyResult] = []

    for study_uid, study_files in studies.items():
        series_groups: dict[str, list[FileResult]] = defaultdict(list)
        for f in study_files:
            suid = f.series_instance_uid or "MISSING_SERIES_UID"
            series_groups[suid].append(f)

        series_results: list[SeriesResult] = []
        for series_uid, series_files in series_groups.items():
            series_findings = run_series_checks(series_files)

            series_results.append(
                SeriesResult(
                    study_instance_uid=study_uid,
                    series_instance_uid=series_uid,
                    modality=series_files[0].modality if series_files else None,
                    file_results=series_files,
                    series_findings=series_findings,
                )
            )

        study_results.append(
            StudyResult(
                study_instance_uid=study_uid,
                series_results=series_results,
            )
        )

    private_findings: list[Finding] = run_privacy_checks(file_results)

    duplicate_uids = _find_duplicate_sop_instance_uids(file_results)
    same_uid_diff_hash = _find_same_uid_different_hash(file_results)

    missing_ids = _find_missing_study_series(file_results, invalid_files)
    duplicate_dataset_findings = _build_duplicate_findings(
        duplicate_uids, same_uid_diff_hash, missing_ids
    )

    patient_ids = set()
    for r in file_results:
        if r.patient_id:
            patient_ids.add(r.patient_id)

    dataset_findings = duplicate_dataset_findings + private_findings

    report = ScanReport(
        dataset_findings=dataset_findings,
        study_results=study_results,
        files_analyzed=len(candidates),
        valid_dicom_count=len(file_results),
        invalid_dicom_count=len(invalid_files),
        series_count=sum(
            len(s.series_results) for s in study_results
        ),
        study_count=len(study_results),
        patient_count=len(patient_ids),
        duplicate_sop_instance_uids=[
            (uid, files) for uid, files in duplicate_uids.items()
        ],
        files_with_same_uid_different_hash=[
            (uid, files) for uid, files in same_uid_diff_hash.items()
        ],
        missing_study_series_ids=missing_ids,
    )

    return apply_scan_profile(report, profile)


def _discover_candidates(directory: Path) -> list[Path]:
    files: list[Path] = []
    for entry in directory.rglob("*"):
        if entry.is_file() and not entry.name.startswith("."):
            files.append(entry)
    return sorted(files)


def _find_duplicate_sop_instance_uids(
    file_results: list[FileResult],
) -> dict[str, list[str]]:
    uid_map: dict[str, list[str]] = defaultdict(list)
    for r in file_results:
        if r.sop_instance_uid:
            uid_map[r.sop_instance_uid].append(r.path)
    return {uid: paths for uid, paths in uid_map.items() if len(paths) > 1}


def _find_same_uid_different_hash(
    file_results: list[FileResult],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    uid_map: dict[str, list[FileResult]] = defaultdict(list)
    for r in file_results:
        if r.sop_instance_uid and r.content_hash:
            uid_map[r.sop_instance_uid].append(r)

    for uid, results in uid_map.items():
        if len(results) < 2:
            continue
        hashes = {r.content_hash for r in results if r.content_hash}
        if len(hashes) > 1:
            result[uid] = [r.path for r in results]
    return result


def _find_missing_study_series(
    valid_results: list[FileResult],
    invalid_results: list[FileResult],
) -> list[str]:
    missing: list[str] = []
    for r in valid_results + invalid_results:
        if r.study_instance_uid is None:
            missing.append(r.path)
        elif r.series_instance_uid is None:
            missing.append(r.path)
    return missing


def _build_duplicate_findings(
    duplicate_uids: dict[str, list[str]],
    same_uid_diff_hash: dict[str, list[str]],
    missing_ids: list[str],
) -> list[Finding]:
    findings: list[Finding] = []

    for uid, paths in duplicate_uids.items():
        findings.append(
            Finding(
                rule_id="DSET-001",
                severity=Severity.ERROR,
                scope=Scope.DATASET,
                message=f"Duplicate SOPInstanceUID '{uid}' found in {len(paths)} files",
                remediation="Each SOPInstanceUID must be unique across the dataset",
                affected_file_count=len(paths),
            )
        )

    for uid, paths in same_uid_diff_hash.items():
        findings.append(
            Finding(
                rule_id="DSET-002",
                severity=Severity.ERROR,
                scope=Scope.DATASET,
                message=f"Files sharing SOPInstanceUID '{uid}' have different content (hash mismatch)",
                remediation="Files with the same SOPInstanceUID must have identical content",
                affected_file_count=len(paths),
            )
        )

    if missing_ids:
        findings.append(
            Finding(
                rule_id="DSET-003",
                severity=Severity.WARNING,
                scope=Scope.DATASET,
                message=f"{len(missing_ids)} file(s) are missing StudyInstanceUID or SeriesInstanceUID",
                remediation="Assign valid UIDs to all DICOM files for proper grouping",
                affected_file_count=len(missing_ids),
            )
        )

    return findings

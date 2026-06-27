from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any

from radscan_lite.models import Finding, ScanReport


def generate_csv_report(report: ScanReport) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "rule_id",
            "severity",
            "scope",
            "message",
            "remediation",
            "affected_file_count",
        ]
    )

    all_findings = list(report.dataset_findings)
    for study in report.study_results:
        all_findings.extend(study.study_findings)
        for series in study.series_results:
            all_findings.extend(series.series_findings)
            for fr in series.file_results:
                all_findings.extend(fr.findings)

    seen: set[tuple] = set()
    for f in all_findings:
        key = (f.rule_id, f.scope, f.message)
        if key not in seen:
            seen.add(key)
            writer.writerow(
                [
                    f.rule_id,
                    f.severity.value,
                    f.scope.value,
                    f.message,
                    f.remediation,
                    f.affected_file_count,
                ]
            )

    return output.getvalue()


def generate_json_report(report: ScanReport) -> str:
    data = _report_to_dict(report)
    return json.dumps(data, indent=2)


def _finding_to_dict(f: Finding) -> dict[str, Any]:
    return {
        "rule_id": f.rule_id,
        "severity": f.severity.value,
        "scope": f.scope.value,
        "message": f.message,
        "remediation": f.remediation,
        "affected_file_count": f.affected_file_count,
    }


def _report_to_dict(report: ScanReport) -> dict[str, Any]:
    findings: list[dict[str, Any]] = [
        _finding_to_dict(f) for f in report.dataset_findings
    ]

    studies_data = []
    for study in report.study_results:
        study_findings = [_finding_to_dict(f) for f in study.study_findings]
        series_data = []
        for series in study.series_results:
            series_findings = [
                _finding_to_dict(f) for f in series.series_findings
            ]
            file_data = []
            for fr in series.file_results:
                file_findings = [
                    _finding_to_dict(f) for f in fr.findings
                ]
                file_data.append(
                    {
                        "path": fr.path,
                        "is_valid_dicom": fr.is_valid_dicom,
                        "sop_class_uid": fr.sop_class_uid,
                        "sop_instance_uid": fr.sop_instance_uid,
                        "modality": fr.modality,
                        "findings": file_findings,
                    }
                )
            series_data.append(
                {
                    "series_instance_uid": series.series_instance_uid,
                    "modality": series.modality,
                    "file_count": len(series.file_results),
                    "findings": series_findings,
                    "files": file_data,
                }
            )
        studies_data.append(
            {
                "study_instance_uid": study.study_instance_uid,
                "series_count": len(study.series_results),
                "findings": study_findings,
                "series": series_data,
            }
        )

    return {
        "profile_name": report.profile_name,
        "profile_description": report.profile_description,
        "scan_timestamp": report.scan_timestamp,
        "files_analyzed": report.files_analyzed,
        "valid_dicom_count": report.valid_dicom_count,
        "invalid_dicom_count": report.invalid_dicom_count,
        "patient_count": report.patient_count,
        "study_count": report.study_count,
        "series_count": report.series_count,
        "duplicate_sop_instance_uids": [
            {"uid": uid, "files": files}
            for uid, files in report.duplicate_sop_instance_uids
        ],
        "files_with_same_uid_different_hash": [
            {"uid": uid, "files": files}
            for uid, files in report.files_with_same_uid_different_hash
        ],
        "dataset_findings": findings,
        "studies": studies_data,
    }

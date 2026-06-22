from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add scripts dir to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from generate_synthetic_data import generate_dataset
from radscan_lite.reporting import generate_csv_report, generate_json_report
from radscan_lite.scanner import scan_directory


def run_demo(output_dir: str) -> dict:
    out = output_dir
    reports_dir = os.path.join(out, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    data_dir = tempfile.mkdtemp(prefix="radscan_demo_data_")
    generate_dataset(data_dir)

    report = scan_directory(data_dir)

    summary = {
        "files_analyzed": report.files_analyzed,
        "valid_dicom_count": report.valid_dicom_count,
        "invalid_dicom_count": report.invalid_dicom_count,
        "study_count": report.study_count,
        "series_count": report.series_count,
        "patient_count": report.patient_count,
        "duplicate_uids": len(report.duplicate_sop_instance_uids),
        "hash_mismatches": len(report.files_with_same_uid_different_hash),
        "missing_ids": len(report.missing_study_series_ids),
    }

    def _finding_dict(f):
        return {
            "rule_id": f.rule_id,
            "severity": f.severity.value,
            "scope": f.scope.value,
            "message": f.message,
            "remediation": f.remediation,
            "affected_file_count": f.affected_file_count,
        }

    all_findings = [_finding_dict(f) for f in report.dataset_findings]
    for study in report.study_results:
        all_findings.extend(_finding_dict(f) for f in study.study_findings)
        for series in study.series_results:
            all_findings.extend(_finding_dict(f) for f in series.series_findings)
            for fr in series.file_results:
                all_findings.extend(_finding_dict(f) for f in fr.findings)

    severity_counts = {}
    for f in all_findings:
        sev = f["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    result = {
        "summary": summary,
        "severity_counts": severity_counts,
        "total_findings": len(all_findings),
        "findings_sample": all_findings[:50],
    }

    with open(os.path.join(reports_dir, "demo_results.json"), "w") as fp:
        json.dump(result, fp, indent=2)

    csv_data = generate_csv_report(report)
    with open(os.path.join(reports_dir, "radscan_report.csv"), "w", newline="") as fp:
        fp.write(csv_data)

    json_data = generate_json_report(report)
    with open(os.path.join(reports_dir, "radscan_report.json"), "w") as fp:
        fp.write(json_data)

    # Cleanup temp data
    import shutil
    shutil.rmtree(data_dir, ignore_errors=True)

    print(f"\n{'='*60}")
    print(f"  RadScan Lite — Demo Results")
    print(f"{'='*60}")
    print(f"  Files analyzed:     {summary['files_analyzed']}")
    print(f"  Valid DICOM:        {summary['valid_dicom_count']}")
    print(f"  Invalid DICOM:      {summary['invalid_dicom_count']}")
    print(f"  Studies found:      {summary['study_count']}")
    print(f"  Series found:       {summary['series_count']}")
    print(f"  Patients detected:  {summary['patient_count']}")
    print(f"  Total findings:     {result['total_findings']}")
    print(f"{'='*60}")
    print(f"  Findings by severity:")
    for sev, count in sorted(severity_counts.items()):
        print(f"    {sev:20s}: {count}")
    print(f"{'='*60}")
    print(f"  Reports saved to: {reports_dir}")
    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_assets")
    os.makedirs(out_dir, exist_ok=True)
    run_demo(out_dir)

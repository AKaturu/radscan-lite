from __future__ import annotations

import pydicom
from pydicom.dataset import Dataset

from radscan_lite.models import FileResult, Finding, Scope, Severity


_PHI_KEYWORDS = [
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "AccessionNumber",
    "InstitutionName",
    "ReferringPhysicianName",
    "PerformingPhysicianName",
    "OperatorsName",
    "StudyComments",
    "AdditionalPatientHistory",
    "MedicalAlerts",
    "ContrastAllergies",
    "SpecialNeeds",
    "PatientComments",
    "RequestingPhysician",
    "NameOfPhysiciansReadingStudy",
    "PhysiciansOfRecord",
]


def run_privacy_checks(file_results: list[FileResult]) -> list[Finding]:
    findings: list[Finding] = []

    for result in file_results:
        if not result.is_valid_dicom:
            continue

        ds = _safe_read(result.path)
        if ds is None:
            continue

        for keyword in _PHI_KEYWORDS:
            _check_phi_tag(result, ds, keyword, findings)

        _check_patient_identity_removed(result, ds, findings)
        _check_deidentification_method(result, ds, findings)
        _check_burned_in_annotation(result, findings)
        _check_private_tags(result, findings)

    return _deduplicate_findings(findings)


def _safe_read(path: str) -> Dataset | None:
    try:
        return pydicom.dcmread(path, force=True, stop_before_pixels=True)
    except Exception:
        return None


def _check_phi_tag(
    result: FileResult,
    ds: Dataset,
    keyword: str,
    findings: list[Finding],
) -> None:
    from pydicom.datadict import tag_for_keyword
    from pydicom.tag import Tag

    tag_val = tag_for_keyword(keyword)
    if tag_val is None:
        return
    tag = Tag(tag_val)
    if tag not in ds:
        return

    elem = ds[tag]
    raw = elem.value
    if raw is None:
        return

    val_str = str(raw).strip()
    status = "blank" if not val_str else "present"

    findings.append(
        Finding(
            rule_id=f"PRIV-{keyword.upper()}",
            severity=Severity.WARNING,
            scope=Scope.FILE,
            message=f"PHI field '{keyword}' is {status} (value not displayed)",
            remediation="De-identify or remove this field before sharing the dataset",
            affected_file_count=1,
        )
    )


def _get_tag_value(
    ds: Dataset, keyword: str
) -> str | None:
    from pydicom.datadict import tag_for_keyword
    from pydicom.tag import Tag

    tag_val = tag_for_keyword(keyword)
    if tag_val is None:
        return None
    tag = Tag(tag_val)
    if tag not in ds:
        return None
    raw = ds[tag].value
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def _check_patient_identity_removed(
    result: FileResult, ds: Dataset, findings: list[Finding]
) -> None:
    val = _get_tag_value(ds, "PatientIdentityRemoved")
    if val is None:
        findings.append(
            Finding(
                rule_id="PRIV-PATIENT_IDENTITY_REMOVED",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="PatientIdentityRemoved (0012,0062) is missing — de-identification status unknown",
                remediation="Add PatientIdentityRemoved to document de-identification status",
                affected_file_count=1,
            )
        )
    elif val == "YES":
        return
    elif val == "NO":
        findings.append(
            Finding(
                rule_id="PRIV-PATIENT_IDENTITY_REMOVED",
                severity=Severity.WARNING,
                scope=Scope.FILE,
                message="PatientIdentityRemoved is NO — patient identity has not been removed",
                remediation="De-identify the dataset or set PatientIdentityRemoved to YES",
                affected_file_count=1,
            )
        )
    else:
        findings.append(
            Finding(
                rule_id="PRIV-PATIENT_IDENTITY_REMOVED",
                severity=Severity.WARNING,
                scope=Scope.FILE,
                message=f"PatientIdentityRemoved has unexpected value: '{val}'",
                remediation="Set PatientIdentityRemoved to YES or NO",
                affected_file_count=1,
            )
        )


def _check_deidentification_method(
    result: FileResult, ds: Dataset, findings: list[Finding]
) -> None:
    val = _get_tag_value(ds, "DeidentificationMethod")
    if val is None:
        findings.append(
            Finding(
                rule_id="PRIV-DEIDENTIFICATION_METHOD",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="DeidentificationMethod is missing — de-identification approach unknown",
                remediation="Document the de-identification method used",
                affected_file_count=1,
            )
        )
    elif val:
        findings.append(
            Finding(
                rule_id="PRIV-DEIDENTIFICATION_METHOD",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="DeidentificationMethod is present",
                remediation="Verify the method used is appropriate for your use case",
                affected_file_count=1,
            )
        )
    else:
        findings.append(
            Finding(
                rule_id="PRIV-DEIDENTIFICATION_METHOD",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="DeidentificationMethod is blank",
                remediation="Document the de-identification method used",
                affected_file_count=1,
            )
        )


def _check_burned_in_annotation(
    result: FileResult, findings: list[Finding]
) -> None:
    bia = result.burn_in_annotation
    if bia is None or not bia.strip():
        findings.append(
            Finding(
                rule_id="PRIV-BURNED_IN_ANNOTATION",
                severity=Severity.MANUAL_REVIEW,
                scope=Scope.FILE,
                message="BurnedInAnnotation is missing or blank — visual review required",
                remediation="Visually inspect images for burned-in annotations",
                affected_file_count=1,
            )
        )
    elif bia.strip().upper() == "YES":
        findings.append(
            Finding(
                rule_id="PRIV-BURNED_IN_ANNOTATION",
                severity=Severity.ERROR,
                scope=Scope.FILE,
                message="BurnedInAnnotation is YES — images may contain burned-in patient information",
                remediation="Remove or obscure burned-in annotations before sharing",
                affected_file_count=1,
            )
        )
    elif bia.strip().upper() == "NO":
        findings.append(
            Finding(
                rule_id="PRIV-BURNED_IN_ANNOTATION",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="BurnedInAnnotation is NO — this is not proof that pixels are free of identifying info",
                remediation="Visual review is still recommended for sensitive datasets",
                affected_file_count=1,
            )
        )


def _check_private_tags(
    result: FileResult, findings: list[Finding]
) -> None:
    if result.has_private_tags:
        findings.append(
            Finding(
                rule_id="PRIV-PRIVATE_TAGS",
                severity=Severity.INFO,
                scope=Scope.FILE,
                message="Private tags are present — may contain identifying information",
                remediation="Review private tags for any embedded PHI and remove if necessary",
                affected_file_count=1,
            )
        )


def _deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple] = set()
    unique: list[Finding] = []
    for f in findings:
        key = (f.rule_id, f.scope, f.message, f.severity)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique

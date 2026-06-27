from __future__ import annotations

from dataclasses import dataclass, field

from radscan_lite.models import Finding, ScanReport, Severity


@dataclass(frozen=True)
class ScanProfile:
    name: str
    description: str
    suppress_rules: tuple[str, ...] = ()
    suppress_prefixes: tuple[str, ...] = ()
    severity_overrides: dict[str, Severity] = field(default_factory=dict)


BUILT_IN_PROFILES: dict[str, ScanProfile] = {
    "full": ScanProfile(
        name="full",
        description="Run and report all structural, series, dataset, and privacy checks.",
    ),
    "structure-only": ScanProfile(
        name="structure-only",
        description="Report structural, series, and dataset findings while hiding privacy-review rules.",
        suppress_prefixes=("PRIV-",),
    ),
    "sharing-review": ScanProfile(
        name="sharing-review",
        description="Emphasize findings relevant before sharing a dataset outside the local team.",
        severity_overrides={
            "PRIV-PRIVATE_TAGS": Severity.WARNING,
            "PRIV-DEIDENTIFICATION_METHOD": Severity.WARNING,
        },
    ),
}


def get_scan_profile(name: str | ScanProfile | None) -> ScanProfile:
    if isinstance(name, ScanProfile):
        return name
    key = name or "full"
    try:
        return BUILT_IN_PROFILES[key]
    except KeyError as exc:
        options = ", ".join(sorted(BUILT_IN_PROFILES))
        raise ValueError(f"Unknown scan profile '{key}'. Available profiles: {options}") from exc


def apply_scan_profile(report: ScanReport, profile: str | ScanProfile | None) -> ScanReport:
    selected = get_scan_profile(profile)
    profiled = report.model_copy(
        update={
            "profile_name": selected.name,
            "profile_description": selected.description,
        },
        deep=True,
    )
    if selected.name == "full":
        return profiled

    profiled.dataset_findings = _apply_to_findings(profiled.dataset_findings, selected)
    for study in profiled.study_results:
        study.study_findings = _apply_to_findings(study.study_findings, selected)
        for series in study.series_results:
            series.series_findings = _apply_to_findings(series.series_findings, selected)
            for file_result in series.file_results:
                file_result.findings = _apply_to_findings(file_result.findings, selected)
    return profiled


def _apply_to_findings(findings: list[Finding], profile: ScanProfile) -> list[Finding]:
    output: list[Finding] = []
    for finding in findings:
        if finding.rule_id in profile.suppress_rules:
            continue
        if any(finding.rule_id.startswith(prefix) for prefix in profile.suppress_prefixes):
            continue
        severity = profile.severity_overrides.get(finding.rule_id)
        output.append(finding.model_copy(update={"severity": severity}) if severity else finding)
    return output

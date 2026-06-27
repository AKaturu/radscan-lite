from __future__ import annotations

import os
import tempfile

import streamlit as st

from radscan_lite.archive_security import cleanup_temp_dir, safe_extract_zip
from radscan_lite.profiles import BUILT_IN_PROFILES
from radscan_lite.reporting import generate_csv_report, generate_json_report
from radscan_lite.scanner import scan_directory
from radscan_lite.thumbnails import generate_thumbnail


def _collect_all_findings(report):
    findings = list(report.dataset_findings)
    for study in report.study_results:
        findings.extend(study.study_findings)
        for series in study.series_results:
            findings.extend(series.series_findings)
            for fr in series.file_results:
                findings.extend(fr.findings)
    return findings


def _collect_all_file_results(report):
    results = []
    for study in report.study_results:
        for series in study.series_results:
            results.extend(series.file_results)
    return results


st.set_page_config(
    page_title="RadScan Lite",
    page_icon="🩻",
    layout="wide",
)

st.title("RadScan Lite - DICOM Dataset Preflight Scanner")
st.markdown(
    "Upload DICOM files or a ZIP archive for structural and privacy preflight scanning. "
    "No data is persisted or transmitted."
)

if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = None
if "report" not in st.session_state:
    st.session_state.report = None
if "scan_complete" not in st.session_state:
    st.session_state.scan_complete = False


_uploaded_files = st.file_uploader(
    "Upload DICOM files or a ZIP archive",
    type=["zip", "dcm"],
    accept_multiple_files=True,
)

profile_name = st.sidebar.selectbox(
    "Check profile",
    options=list(BUILT_IN_PROFILES),
    index=0,
    format_func=lambda name: name.replace("-", " ").title(),
)
st.sidebar.caption(BUILT_IN_PROFILES[profile_name].description)

if _uploaded_files:
    temp_dir = tempfile.mkdtemp(prefix="radscan_upload_")
    st.session_state.temp_dir = temp_dir

    extracted_dirs = []
    with st.spinner("Processing uploads..."):
        for uploaded_file in _uploaded_files:
            fpath = os.path.join(temp_dir, uploaded_file.name)
            with open(fpath, "wb") as f:
                f.write(uploaded_file.getbuffer())

            if uploaded_file.name.lower().endswith(".zip"):
                try:
                    extract_path = safe_extract_zip(fpath)
                    extracted_dirs.append(extract_path)
                except ValueError as e:
                    st.error(f"Archive error in '{uploaded_file.name}': {e}")

        all_paths = [temp_dir] + extracted_dirs
        combined_dir = tempfile.mkdtemp(prefix="radscan_combined_")
        extracted_dirs.append(combined_dir)

        import shutil

        for src_dir in [temp_dir] + extracted_dirs[:-1]:
            if os.path.isdir(src_dir):
                for item in os.listdir(src_dir):
                    s = os.path.join(src_dir, item)
                    d = os.path.join(combined_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)

        st.session_state.report = scan_directory(combined_dir, profile=profile_name)
        st.session_state.scan_complete = True

if st.session_state.scan_complete and st.session_state.report:
    report = st.session_state.report

    st.subheader("Overall Status")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Files Found", report.files_analyzed)
    col2.metric("Valid DICOM", report.valid_dicom_count)
    col3.metric("Invalid", report.invalid_dicom_count)
    col4.metric("Studies", report.study_count)
    col5.metric("Series", report.series_count)
    col6.metric("Patients", report.patient_count)

    all_findings = _collect_all_findings(report)
    severity_order = {
        "ERROR": 0,
        "WARNING": 1,
        "MANUAL REVIEW": 2,
        "INFO": 3,
        "PASS": 4,
    }
    all_findings.sort(key=lambda f: severity_order.get(f.severity.value, 99))

    st.subheader("Findings by Severity")
    for sev_label, sev_color in [
        ("ERROR", "red"),
        ("WARNING", "orange"),
        ("MANUAL REVIEW", "yellow"),
        ("INFO", "blue"),
        ("PASS", "green"),
    ]:
        sev_findings = [
            f for f in all_findings if f.severity.value == sev_label
        ]
        if sev_findings:
            with st.expander(
                f"{sev_label} ({len(sev_findings)})", expanded=sev_label == "ERROR"
            ):
                for f in sev_findings:
                    st.markdown(
                        f"**{f.rule_id}** — {f.message}  \n"
                        f"*Remediation:* {f.remediation}  \n"
                        f"*Scope:* {f.scope.value}  *Affected files:* {f.affected_file_count}"
                    )

    st.subheader("Study Summary")
    study_data = []
    for study in report.study_results:
        total_findings = len(study.study_findings) + sum(
            len(s.series_findings) for s in study.series_results
        )
        study_data.append(
            {
                "Study UID": study.study_instance_uid,
                "Series Count": len(study.series_results),
                "Findings": total_findings,
            }
        )
    if study_data:
        st.dataframe(study_data, use_container_width=True)
    else:
        st.info("No valid studies found.")

    st.subheader("Series Summary")
    series_data = []
    for study in report.study_results:
        for series in study.series_results:
            series_data.append(
                {
                    "Study UID": series.study_instance_uid[:20] + "...",
                    "Series UID": series.series_instance_uid[:20] + "...",
                    "Modality": series.modality or "N/A",
                    "Files": len(series.file_results),
                    "Findings": len(series.series_findings),
                }
            )
    if series_data:
        st.dataframe(series_data, use_container_width=True)
    else:
        st.info("No valid series found.")

    st.subheader("Invalid Files")
    invalid_files = []
    for result in _collect_all_file_results(report):
        if not result.is_valid_dicom:
            invalid_files.append(result)
    if invalid_files:
        table_data = []
        for f in invalid_files:
            table_data.append(
                {
                    "Path": f.path,
                    "Findings": "; ".join(
                        f"{fi.rule_id}: {fi.message}" for fi in f.findings
                    ),
                }
            )
        st.dataframe(table_data, use_container_width=True)
    else:
        st.success("No invalid DICOM files found.")

    st.subheader("Privacy Warnings")
    privacy_findings = [
        f for f in all_findings if f.rule_id.startswith("PRIV-")
    ]
    if privacy_findings:
        for f in privacy_findings:
            sev_label = f.severity.value
            st.markdown(
                f"**{f.rule_id}** [{sev_label}] — {f.message}  \n"
                f"*Remediation:* {f.remediation}"
            )
    else:
        st.info("No privacy warnings detected.")

    st.subheader("Representative Series Thumbnails")
    st.markdown(
        "*Thumbnails are for technical review only. "
        "Do not use for diagnostic purposes.*"
    )
    thumbnail_count = 0
    for study in report.study_results:
        for series in study.series_results:
            for fr in series.file_results:
                thumb = generate_thumbnail(fr)
                if thumb:
                    st.image(thumb, caption=f"{series.modality} — {fr.path}", width=256)
                    thumbnail_count += 1
                    break
            if thumbnail_count >= 10:
                break
        if thumbnail_count >= 10:
            break
    if thumbnail_count == 0:
        st.info("No thumbnails could be generated from the uploaded files.")

    st.subheader("Download Reports")
    csv_data = generate_csv_report(report)
    json_data = generate_json_report(report)

    st.download_button(
        label="Download CSV Report",
        data=csv_data,
        file_name="radscan_report.csv",
        mime="text/csv",
    )
    st.download_button(
        label="Download JSON Report",
        data=json_data,
        file_name="radscan_report.json",
        mime="application/json",
    )

    st.subheader("Disclaimer")
    st.warning(
        "RadScan Lite is a preflight quality-assurance tool for DICOM datasets. "
        "It does not diagnose disease, modify files, establish HIPAA compliance, "
        "or guarantee full de-identification. "
        "Always visually review images and verify compliance with applicable regulations."
    )

if st.button("Clear & Start Over"):
    if st.session_state.temp_dir and os.path.isdir(st.session_state.temp_dir):
        cleanup_temp_dir(st.session_state.temp_dir)
    st.session_state.temp_dir = None
    st.session_state.report = None
    st.session_state.scan_complete = False
    st.rerun()



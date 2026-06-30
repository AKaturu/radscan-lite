from __future__ import annotations

import json
import os
import sys
import warnings
import zipfile

import pydicom
import pytest
from pydicom.uid import UID, generate_uid

from radscan_lite.archive_security import cleanup_temp_dir, safe_extract_zip
from radscan_lite.dicom_reader import has_dicm_prefix, read_file_result
from radscan_lite.file_checks import run_file_checks
from radscan_lite.models import FileResult, Severity
from radscan_lite.privacy_checks import run_privacy_checks
from radscan_lite.profiles import apply_scan_profile
from radscan_lite.reporting import generate_csv_report, generate_json_report
from radscan_lite.scanner import scan_directory
from radscan_lite.series_checks import run_series_checks
from radscan_lite.thumbnails import generate_thumbnail

scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
from generate_synthetic_data import _make_dataset, _save_ds


def _file_result_from_ds(ds: pydicom.dataset.Dataset, path: str) -> FileResult:
    _save_ds(ds, path)
    return read_file_result(path)


def _make_file_result(
    study_uid: str,
    series_uid: str,
    sop_uid: str,
    rows: int = 512,
    cols: int = 512,
    instance_number: int = 1,
    pixel_spacing: str = "0.5\\0.5",
    image_orientation: str = "1\\0\\0\\0\\1\\0",
    image_position: str = "0.0\\0.0\\0.0",
    frame_of_reference: str = "FRAME.1",
    modality: str = "CT",
) -> FileResult:
    return FileResult(
        path="/fake/path.dcm",
        is_valid_dicom=True,
        study_instance_uid=study_uid,
        series_instance_uid=series_uid,
        sop_instance_uid=sop_uid,
        rows=rows,
        columns=cols,
        instance_number=instance_number,
        pixel_spacing=pixel_spacing,
        image_orientation_patient=image_orientation,
        image_position_patient=image_position,
        frame_of_reference_uid=frame_of_reference,
        modality=modality,
        pixel_decoding_success=True,
    )


class TestDicomReader:
    def test_valid_ct_file(self, synthetic_dataset):
        path = os.path.join(synthetic_dataset, "clean_series")
        files = sorted(os.listdir(path))
        assert len(files) == 5
        for fname in files:
            fpath = os.path.join(path, fname)
            result = read_file_result(fpath)
            assert result.is_valid_dicom is True
            assert result.sop_class_uid is not None
            assert result.sop_instance_uid is not None
            assert result.study_instance_uid is not None
            assert result.series_instance_uid is not None
            assert result.modality == "CT"
            assert result.rows == 512
            assert result.columns == 512

    def test_malformed_file(self, temp_output_dir):
        path = os.path.join(temp_output_dir, "not_dicom.bin")
        with open(path, "wb") as f:
            f.write(b"not a dicom file")
        result = read_file_result(path)
        assert result.is_valid_dicom is False

    def test_missing_uid(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        ds.SOPInstanceUID = None
        path = os.path.join(temp_output_dir, "missing_uid.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        assert result.is_valid_dicom is True
        assert result.sop_instance_uid is None

    def test_dicm_prefix_check(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        path = os.path.join(temp_output_dir, "with_prefix.dcm")
        _save_ds(ds, path)
        assert has_dicm_prefix(path) is True


class TestFileChecks:
    def test_missing_uid_checks(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        ds.StudyInstanceUID = None
        ds.SeriesInstanceUID = None
        path = os.path.join(temp_output_dir, "missing_uids.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        result.findings = run_file_checks(result)
        rule_ids = {f.rule_id for f in result.findings}
        assert "FILE-005" in rule_ids
        assert "FILE-006" in rule_ids

    def test_pixel_data_decoding(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        path = os.path.join(temp_output_dir, "good_pixels.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        assert result.pixel_decoding_success is True

    def test_corrupt_pixel_data(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        ds.PixelData = b"not enough pixel data here"
        path = os.path.join(temp_output_dir, "corrupt_pixels.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        result.findings = run_file_checks(result)
        rule_ids = {f.rule_id for f in result.findings}
        assert "FILE-008" in rule_ids or "FILE-009" in rule_ids


class TestSeriesChecks:
    def test_inconsistent_dimensions(self):
        study_uid = generate_uid()
        series_uid = generate_uid()
        files = [
            _make_file_result(study_uid, series_uid, generate_uid(), rows=512, cols=512, instance_number=1),
            _make_file_result(study_uid, series_uid, generate_uid(), rows=256, cols=256, instance_number=2),
        ]
        findings = run_series_checks(files)
        rule_ids = {f.rule_id for f in findings}
        assert "SERIES-001" in rule_ids
        assert "SERIES-002" in rule_ids

    def test_duplicate_instance_number(self):
        study_uid = generate_uid()
        series_uid = generate_uid()
        files = [
            _make_file_result(study_uid, series_uid, generate_uid(), instance_number=1),
            _make_file_result(study_uid, series_uid, generate_uid(), instance_number=1),
        ]
        findings = run_series_checks(files)
        rule_ids = {f.rule_id for f in findings}
        assert "SERIES-006" in rule_ids


class TestPrivacyChecks:
    def test_phi_tag_present(self, synthetic_dataset):
        path = os.path.join(synthetic_dataset, "privacy_series")
        files = sorted(os.listdir(path))
        file_results = []
        for fname in files:
            fr = read_file_result(os.path.join(path, fname))
            file_results.append(fr)
        findings = run_privacy_checks(file_results)
        rule_ids = {f.rule_id for f in findings}
        priv_rules = {r for r in rule_ids if r.startswith("PRIV-")}
        assert "PRIV-PATIENTNAME" in priv_rules
        assert "PRIV-PATIENTID" in priv_rules

    def test_burned_in_annotation_yes(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
            burn_in_annotation="YES",
        )
        path = os.path.join(temp_output_dir, "bia_yes.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        findings = run_privacy_checks([result])
        bia_findings = [f for f in findings if f.rule_id == "PRIV-BURNED_IN_ANNOTATION"]
        assert len(bia_findings) == 1
        assert bia_findings[0].severity == Severity.ERROR

    def test_burned_in_annotation_no(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
            burn_in_annotation="NO",
        )
        path = os.path.join(temp_output_dir, "bia_no.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        findings = run_privacy_checks([result])
        bia_findings = [f for f in findings if f.rule_id == "PRIV-BURNED_IN_ANNOTATION"]
        assert len(bia_findings) == 1
        assert bia_findings[0].severity == Severity.INFO

    def test_burned_in_annotation_missing(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        path = os.path.join(temp_output_dir, "bia_missing.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        findings = run_privacy_checks([result])
        bia_findings = [f for f in findings if f.rule_id == "PRIV-BURNED_IN_ANNOTATION"]
        assert len(bia_findings) == 1
        assert bia_findings[0].severity == Severity.MANUAL_REVIEW

    def test_private_tags_detected(self, synthetic_dataset):
        path = os.path.join(synthetic_dataset, "privacy_series")
        file_results = []
        for fname in sorted(os.listdir(path)):
            fr = read_file_result(os.path.join(path, fname))
            file_results.append(fr)
        findings = run_privacy_checks(file_results)
        priv_tag_findings = [f for f in findings if f.rule_id == "PRIV-PRIVATE_TAGS"]
        assert len(priv_tag_findings) >= 1

    def test_phi_values_not_in_reports(self, synthetic_dataset):
        """Confirm that identifying values never appear in reports or logs."""
        report = scan_directory(synthetic_dataset)
        csv_output = generate_csv_report(report)
        json_output = generate_json_report(report)

        phi_patterns = ["DOE^JOHN", "SMITH^JANE", "ID123456", "19700101", "123 Main St"]
        for pattern in phi_patterns:
            assert pattern not in csv_output, f"PHI value '{pattern}' found in CSV report"
            assert pattern not in json_output, f"PHI value '{pattern}' found in JSON report"


class TestThumbnails:
    def test_monochrome1_thumbnail(self, temp_output_dir):
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        ds.PhotometricInterpretation = "MONOCHROME1"
        path = os.path.join(temp_output_dir, "mono1.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        thumb = generate_thumbnail(result)
        assert thumb is not None
        assert isinstance(thumb, bytes)

    def test_thumbnail_generation(self, synthetic_dataset):
        path = os.path.join(synthetic_dataset, "clean_series")
        files = sorted(os.listdir(path))
        fpath = os.path.join(path, files[0])
        result = read_file_result(fpath)
        thumb = generate_thumbnail(result)
        assert thumb is not None
        assert isinstance(thumb, bytes)


class TestScanner:
    def test_scan_synthetic_dataset(self, synthetic_dataset):
        report = scan_directory(synthetic_dataset)
        assert report.files_analyzed == 15
        assert report.valid_dicom_count == 15
        assert report.invalid_dicom_count == 0
        assert report.study_count == 3
        assert report.series_count == 3

    def test_scan_clean_series(self, synthetic_dataset):
        path = os.path.join(synthetic_dataset, "clean_series")
        report = scan_directory(path)
        assert report.valid_dicom_count == 5
        assert report.study_count == 1
        assert report.series_count == 1

    def test_scan_inconsistent_series(self, synthetic_dataset):
        path = os.path.join(synthetic_dataset, "inconsistent_series")
        report = scan_directory(path)
        assert report.valid_dicom_count == 5
        series_finding_ids = set()
        for study in report.study_results:
            for series in study.series_results:
                for f in series.series_findings:
                    series_finding_ids.add(f.rule_id)
        assert "SERIES-001" in series_finding_ids
        assert "SERIES-002" in series_finding_ids
        assert "SERIES-003" in series_finding_ids

    def test_scan_privacy_series(self, synthetic_dataset):
        path = os.path.join(synthetic_dataset, "privacy_series")
        report = scan_directory(path)
        priv_rules = {f.rule_id for f in report.dataset_findings if f.rule_id.startswith("PRIV-")}
        assert "PRIV-PATIENTNAME" in priv_rules
        assert "PRIV-PATIENTID" in priv_rules
        assert "PRIV-BURNED_IN_ANNOTATION" in priv_rules

    def test_duplicate_sop_uid(self, temp_output_dir):
        study_uid = generate_uid()
        series_uid = generate_uid()
        uid = generate_uid()
        ds1 = _make_dataset(
            study_uid=study_uid, series_uid=series_uid, sop_instance_uid=uid
        )
        ds2 = _make_dataset(
            study_uid=study_uid, series_uid=series_uid, sop_instance_uid=uid
        )
        p1 = os.path.join(temp_output_dir, "dup1.dcm")
        p2 = os.path.join(temp_output_dir, "dup2.dcm")
        _save_ds(ds1, p1)
        _save_ds(ds2, p2)
        report = scan_directory(temp_output_dir)
        assert len(report.duplicate_sop_instance_uids) > 0

    def test_synthetic_frame_of_reference_uids_are_valid(self, synthetic_dataset):
        for subdir in ("clean_series", "inconsistent_series", "privacy_series"):
            path = os.path.join(synthetic_dataset, subdir)
            for fname in sorted(os.listdir(path)):
                ds = pydicom.dcmread(os.path.join(path, fname), stop_before_pixels=True)
                assert UID(ds.FrameOfReferenceUID).is_valid

    def test_synthetic_generation_has_no_pydicom_uid_warnings(self, temp_output_dir):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            from generate_synthetic_data import generate_dataset

            generate_dataset(temp_output_dir)
        messages = [str(item.message) for item in caught]
        assert not any("Invalid value for VR UI" in message for message in messages)
        assert not any("write_like_original" in message for message in messages)


class TestArchiveSecurity:
    def test_zip_extraction(self, temp_output_dir):
        zip_path = os.path.join(temp_output_dir, "test.zip")
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        dcm_path = os.path.join(temp_output_dir, "test.dcm")
        _save_ds(ds, dcm_path)

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(dcm_path, "test.dcm")

        extract_dir = safe_extract_zip(zip_path)
        try:
            extracted = os.listdir(extract_dir)
            assert "test.dcm" in extracted
        finally:
            cleanup_temp_dir(extract_dir)

    def test_empty_zip(self, temp_output_dir):
        zip_path = os.path.join(temp_output_dir, "empty.zip")
        with zipfile.ZipFile(zip_path, "w"):
            pass
        extract_dir = safe_extract_zip(zip_path)
        assert os.path.isdir(extract_dir)
        cleanup_temp_dir(extract_dir)

    def test_compression_ratio_limit(self, temp_output_dir):
        zip_path = os.path.join(temp_output_dir, "bomb.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            info = zipfile.ZipInfo("bomb.txt")
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, b"x" * 10000000)
        with pytest.raises(ValueError):
            safe_extract_zip(zip_path, max_compression_ratio=10)

    def test_cleanup_temp_dir(self, temp_output_dir):
        sub = os.path.join(temp_output_dir, "subdir")
        os.makedirs(sub)
        with open(os.path.join(sub, "test.txt"), "w") as f:
            f.write("hello")
        cleanup_temp_dir(sub)
        assert not os.path.isdir(sub)


class TestReporting:
    def test_csv_report_generation(self, synthetic_dataset):
        report = scan_directory(synthetic_dataset)
        csv_output = generate_csv_report(report)
        assert "rule_id" in csv_output
        assert "severity" in csv_output
        assert "PRIV-" in csv_output
        assert "SERIES-" in csv_output or "FILE-" in csv_output

    def test_json_report_generation(self, synthetic_dataset):
        report = scan_directory(synthetic_dataset)
        json_output = generate_json_report(report)
        assert "scan_timestamp" in json_output
        assert "files_analyzed" in json_output
        assert "studies" in json_output
        assert json.loads(json_output)["profile_name"] == "full"


class TestScanProfiles:
    def test_structure_only_profile_suppresses_privacy_findings(self, synthetic_dataset):
        report = scan_directory(synthetic_dataset, profile="structure-only")
        csv_output = generate_csv_report(report)
        json_output = generate_json_report(report)

        assert report.profile_name == "structure-only"
        assert "PRIV-" not in csv_output
        assert "PRIV-" not in json_output

    def test_sharing_review_profile_overrides_private_tag_severity(self, synthetic_dataset):
        full_report = scan_directory(synthetic_dataset)
        profiled = apply_scan_profile(full_report, "sharing-review")

        private_tag_findings = [
            f for f in profiled.dataset_findings if f.rule_id == "PRIV-PRIVATE_TAGS"
        ]
        assert private_tag_findings
        assert {f.severity for f in private_tag_findings} == {Severity.WARNING}


class TestMultiframe:
    def test_multiframe(self, temp_output_dir):
        import numpy as np
        ds = _make_dataset(
            study_uid=generate_uid(),
            series_uid=generate_uid(),
            sop_instance_uid=generate_uid(),
        )
        ds.NumberOfFrames = 3
        arr = np.random.default_rng(42).integers(0, 2000, size=(3, 128, 128), dtype=np.uint16)
        ds.PixelData = arr.tobytes()
        ds.Rows = 128
        ds.Columns = 128
        path = os.path.join(temp_output_dir, "multiframe.dcm")
        _save_ds(ds, path)
        result = read_file_result(path)
        assert result.number_of_frames == 3

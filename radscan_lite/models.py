from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    PASS = "PASS"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    MANUAL_REVIEW = "MANUAL REVIEW"


class Scope(str, Enum):
    FILE = "file"
    SERIES = "series"
    STUDY = "study"
    DATASET = "dataset"


class Finding(BaseModel):
    rule_id: str
    severity: Severity
    scope: Scope
    message: str
    remediation: str
    affected_file_count: int = 0


class FileResult(BaseModel):
    path: str
    is_valid_dicom: bool = False
    sop_class_uid: Optional[str] = None
    sop_instance_uid: Optional[str] = None
    study_instance_uid: Optional[str] = None
    series_instance_uid: Optional[str] = None
    modality: Optional[str] = None
    patient_id: Optional[str] = None
    content_hash: Optional[str] = None
    findings: list[Finding] = Field(default_factory=list)
    pixel_decoding_success: Optional[bool] = None
    rows: Optional[int] = None
    columns: Optional[int] = None
    number_of_frames: Optional[int] = None
    transfer_syntax_uid: Optional[str] = None
    photometric_interpretation: Optional[str] = None
    samples_per_pixel: Optional[int] = None
    bits_allocated: Optional[int] = None
    bits_stored: Optional[int] = None
    high_bit: Optional[int] = None
    pixel_spacing: Optional[str] = None
    image_orientation_patient: Optional[str] = None
    image_position_patient: Optional[str] = None
    slice_location: Optional[str] = None
    frame_of_reference_uid: Optional[str] = None
    instance_number: Optional[int] = None
    burn_in_annotation: Optional[str] = None
    has_private_tags: bool = False


class SeriesResult(BaseModel):
    study_instance_uid: str
    series_instance_uid: str
    modality: Optional[str] = None
    file_results: list[FileResult] = Field(default_factory=list)
    series_findings: list[Finding] = Field(default_factory=list)


class StudyResult(BaseModel):
    study_instance_uid: str
    series_results: list[SeriesResult] = Field(default_factory=list)
    study_findings: list[Finding] = Field(default_factory=list)


class ScanReport(BaseModel):
    dataset_findings: list[Finding] = Field(default_factory=list)
    study_results: list[StudyResult] = Field(default_factory=list)
    files_analyzed: int = 0
    valid_dicom_count: int = 0
    invalid_dicom_count: int = 0
    series_count: int = 0
    study_count: int = 0
    patient_count: int = 0
    duplicate_sop_instance_uids: list[tuple[str, list[str]]] = Field(
        default_factory=list
    )
    files_with_same_uid_different_hash: list[tuple[str, list[str]]] = Field(
        default_factory=list
    )
    missing_study_series_ids: list[str] = Field(default_factory=list)
    scan_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import pydicom
from pydicom.errors import InvalidDicomError

from radscan_lite.models import FileResult


_DICM_MARKER = b"DICM"


def has_dicm_prefix(filepath: str | Path) -> bool:
    with open(filepath, "rb") as f:
        header = f.read(132)
    return header[128:132] == _DICM_MARKER


def compute_content_hash(filepath: str | Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_dicom_file(filepath: str | Path) -> Optional[pydicom.dataset.Dataset]:
    try:
        ds = pydicom.dcmread(filepath, force=True, stop_before_pixels=False)
        return ds
    except (InvalidDicomError, Exception):
        return None


def _is_plausible_dicom(ds: pydicom.dataset.Dataset) -> bool:
    from pydicom.datadict import tag_for_keyword
    from pydicom.tag import Tag
    for keyword in ("SOPClassUID", "SOPInstanceUID", "PatientName", "Modality"):
        tag_val = tag_for_keyword(keyword)
        if tag_val is not None and Tag(tag_val) in ds:
            return True
    return False


def read_file_result(filepath: str | Path) -> FileResult:
    path_str = str(filepath)
    result = FileResult(path=path_str)
    result.content_hash = compute_content_hash(filepath)

    ds = parse_dicom_file(filepath)
    if ds is None:
        result.is_valid_dicom = False
        return result

    if not _is_plausible_dicom(ds):
        result.is_valid_dicom = False
        return result

    result.is_valid_dicom = True

    result.sop_class_uid = _get_str(ds, "SOPClassUID")
    result.sop_instance_uid = _get_str(ds, "SOPInstanceUID")
    result.study_instance_uid = _get_str(ds, "StudyInstanceUID")
    result.series_instance_uid = _get_str(ds, "SeriesInstanceUID")
    result.modality = _get_str(ds, "Modality")
    result.patient_id = _get_str(ds, "PatientID")
    result.transfer_syntax_uid = _get_str(ds, "TransferSyntaxUID")
    result.photometric_interpretation = _get_str(ds, "PhotometricInterpretation")
    result.samples_per_pixel = _get_int(ds, "SamplesPerPixel")
    result.bits_allocated = _get_int(ds, "BitsAllocated")
    result.bits_stored = _get_int(ds, "BitsStored")
    result.high_bit = _get_int(ds, "HighBit")
    result.rows = _get_int(ds, "Rows")
    result.columns = _get_int(ds, "Columns")
    result.number_of_frames = _get_int(ds, "NumberOfFrames")
    result.pixel_spacing = _get_str(ds, "PixelSpacing")
    result.image_orientation_patient = _get_str(ds, "ImageOrientationPatient")
    result.image_position_patient = _get_str(ds, "ImagePositionPatient")
    result.slice_location = _get_str(ds, "SliceLocation")
    result.frame_of_reference_uid = _get_str(ds, "FrameOfReferenceUID")
    result.instance_number = _get_int(ds, "InstanceNumber")
    result.burn_in_annotation = _get_str(ds, "BurnedInAnnotation")
    result.has_private_tags = _has_private_tags(ds)

    if "PixelData" in ds:
        try:
            _ = ds.pixel_array
            result.pixel_decoding_success = True
        except Exception:
            result.pixel_decoding_success = False
    else:
        result.pixel_decoding_success = None

    return result


def _get_value(
    ds: pydicom.dataset.Dataset, tag: str
) -> object:
    elem = ds.get(tag)
    if elem is None:
        return None
    if hasattr(elem, "value"):
        return elem.value
    return elem


def _get_str(ds: pydicom.dataset.Dataset, tag: str) -> Optional[str]:
    val = _get_value(ds, tag)
    if val is None:
        return None
    val_str = str(val).strip()
    return val_str if val_str else None


def _get_int(ds: pydicom.dataset.Dataset, tag: str) -> Optional[int]:
    val = _get_value(ds, tag)
    if val is None:
        return None
    try:
        if isinstance(val, (list, tuple)):
            return int(val[0])
        return int(val)
    except (ValueError, TypeError):
        return None


def _has_private_tags(ds: pydicom.dataset.Dataset) -> bool:
    for elem in ds:
        if elem.tag.group & 1:
            return True
    return False

from __future__ import annotations

import os
import tempfile

import numpy as np
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid


def _make_meta(sop_class_uid: str, sop_instance_uid: str) -> FileMetaDataset:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = sop_class_uid
    meta.MediaStorageSOPInstanceUID = sop_instance_uid
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    return meta


def _make_ct_pixels(rows: int = 512, cols: int = 512) -> bytes:
    arr = np.random.default_rng(42).integers(0, 2000, size=(rows, cols), dtype=np.uint16)
    return arr.tobytes()


def _make_dataset(
    study_uid: str,
    series_uid: str,
    sop_instance_uid: str,
    modality: str = "CT",
    rows: int = 512,
    cols: int = 512,
    instance_number: int = 1,
    pixel_spacing: str = "0.5\\0.5",
    image_orientation: str = "1\\0\\0\\0\\1\\0",
    image_position: str = "0.0\\0.0\\0.0",
    frame_of_reference: str = "FRAME.1",
    burn_in_annotation: str | None = None,
    patient_name: str | None = None,
    patient_id: str | None = None,
    patient_birth_date: str | None = None,
    patient_address: str | None = None,
    add_private_tags: bool = False,
    corrupt_pixels: bool = False,
) -> bytes:
    ds = Dataset()
    sop_class = "1.2.840.10008.5.1.4.1.1.2"
    ds.file_meta = _make_meta(sop_class, sop_instance_uid)

    ds.SOPClassUID = sop_class
    ds.SOPInstanceUID = sop_instance_uid
    ds.StudyInstanceUID = study_uid
    ds.SeriesInstanceUID = series_uid
    ds.Modality = modality
    ds.PatientName = patient_name or ""
    ds.PatientID = patient_id or ""
    ds.StudyDate = "20260101"
    ds.SeriesNumber = 1
    ds.InstanceNumber = instance_number
    ds.Rows = rows
    ds.Columns = cols

    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0

    ds.PixelSpacing = pixel_spacing
    ds.ImageOrientationPatient = image_orientation
    ds.ImagePositionPatient = image_position
    ds.FrameOfReferenceUID = frame_of_reference
    ds.SliceLocation = str(instance_number * 1.0)

    if burn_in_annotation is not None:
        ds.BurnedInAnnotation = burn_in_annotation

    if patient_birth_date:
        ds.PatientBirthDate = patient_birth_date
    if patient_address:
        ds.PatientAddress = patient_address

    if add_private_tags:
        ds.add_new((0x0041, 0x0010), "LO", "PrivateTagValue")

    if corrupt_pixels:
        ds.PixelData = b"corrupt"
    else:
        ds.PixelData = _make_ct_pixels(rows, cols)

    return ds


def _save_ds(ds: Dataset, path: str) -> str:
    ds.save_as(path, enforce_file_format=True)
    return path


def generate_dataset(output_dir: str) -> str:
    """Generate a synthetic DICOM dataset and return the output directory path."""
    base = output_dir

    study_uid_clean = generate_uid()
    series_uid_clean = generate_uid()
    study_uid_inconsistent = generate_uid()
    series_uid_inconsistent = generate_uid()
    study_uid_privacy = generate_uid()
    series_uid_privacy = generate_uid()

    clean_dir = os.path.join(base, "clean_series")
    inconsistent_dir = os.path.join(base, "inconsistent_series")
    privacy_dir = os.path.join(base, "privacy_series")
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(inconsistent_dir, exist_ok=True)
    os.makedirs(privacy_dir, exist_ok=True)

    for i in range(1, 6):
        ds = _make_dataset(
            study_uid=study_uid_clean,
            series_uid=series_uid_clean,
            sop_instance_uid=generate_uid(),
            modality="CT",
            rows=512,
            cols=512,
            instance_number=i,
            pixel_spacing="0.5\\0.5",
            image_orientation="1\\0\\0\\0\\1\\0",
            image_position=f"0.0\\0.0\\{i * 1.0}",
            frame_of_reference="FRAME.CLEAN",
        )
        _save_ds(ds, os.path.join(clean_dir, f"ct_clean_{i:03d}.dcm"))

    ds_list = []
    for i in range(1, 6):
        kwargs = {
            "study_uid": study_uid_inconsistent,
            "series_uid": series_uid_inconsistent,
            "sop_instance_uid": generate_uid(),
            "modality": "CT" if i <= 4 else "MR",
            "rows": 512 if i % 2 == 0 else 256,
            "cols": 512 if i % 2 == 0 else 256,
            "instance_number": i if i != 3 else 2,
            "pixel_spacing": "0.5\\0.5" if i <= 3 else "1.0\\1.0",
            "image_orientation": "1\\0\\0\\0\\1\\0" if i != 5 else "0\\1\\0\\1\\0\\0",
            "image_position": f"0.0\\0.0\\{i * 3.0}",
            "frame_of_reference": "FRAME.INCONSISTENT",
        }
        ds = _make_dataset(**kwargs)
        _save_ds(ds, os.path.join(inconsistent_dir, f"ct_inconsistent_{i:03d}.dcm"))
        ds_list.append(os.path.join(inconsistent_dir, f"ct_inconsistent_{i:03d}.dcm"))

    privacy_files = [
        {
            "burn_in_annotation": "YES",
            "patient_name": "DOE^JOHN",
            "patient_id": "ID123456",
            "patient_birth_date": "19700101",
        },
        {
            "patient_name": "SMITH^JANE",
            "patient_id": "ID789012",
            "patient_address": "123 Main St",
        },
        {
            "burn_in_annotation": "NO",
            "patient_name": "BROWN^ROBERT",
            "patient_id": "ID345678",
        },
        {
            "patient_name": "JOHNSON^EMILY",
            "patient_id": "ID901234",
            "add_private_tags": True,
        },
        {
            "burn_in_annotation": "YES",
            "patient_name": "WILLIAMS^MICHAEL",
            "patient_id": "ID567890",
            "patient_birth_date": "19850515",
            "add_private_tags": True,
        },
    ]

    for i, kwargs in enumerate(privacy_files, 1):
        ds = _make_dataset(
            study_uid=study_uid_privacy,
            series_uid=series_uid_privacy,
            sop_instance_uid=generate_uid(),
            modality="CT",
            rows=512,
            cols=512,
            instance_number=i,
            frame_of_reference="FRAME.PRIVACY",
            **kwargs,
        )
        _save_ds(ds, os.path.join(privacy_dir, f"ct_privacy_{i:03d}.dcm"))

    return base


if __name__ == "__main__":
    out = tempfile.mkdtemp(prefix="radscan_synthetic_")
    generate_dataset(out)
    print(f"Synthetic data generated at: {out}")
    print("  - Clean series (5 files)")
    print("  - Inconsistent series (5 files)")
    print("  - Privacy-warning series (5 files)")

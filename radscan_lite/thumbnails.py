from __future__ import annotations

from io import BytesIO
from typing import Optional

import numpy as np
from PIL import Image

from radscan_lite.models import FileResult


def generate_thumbnail(
    file_result: FileResult,
    max_size: tuple[int, int] = (256, 256),
) -> Optional[bytes]:
    if not file_result.is_valid_dicom:
        return None
    if file_result.pixel_decoding_success is not True:
        return None

    import pydicom

    try:
        ds = pydicom.dcmread(file_result.path, force=True)
        pixel_array = ds.pixel_array
    except Exception:
        return None

    if pixel_array.ndim < 2 or pixel_array.size == 0:
        return None

    image = _convert_to_8bit(pixel_array, ds)

    image = Image.fromarray(image)
    image.thumbnail(max_size, Image.LANCZOS)

    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _convert_to_8bit(
    pixel_array: np.ndarray, ds: pydicom.dataset.Dataset
) -> np.ndarray:
    if pixel_array.ndim == 3 and pixel_array.shape[2] in (3, 4):
        return _normalize_rgb(pixel_array)

    arr = pixel_array.squeeze()

    if arr.ndim > 2:
        arr = arr[0] if arr.ndim == 3 else arr

    arr = arr.astype(np.float64)

    photometric = str(ds.get("PhotometricInterpretation", "")).strip().upper()

    lower = np.percentile(arr, 1)
    upper = np.percentile(arr, 99)
    if upper <= lower:
        lower = arr.min()
        upper = arr.max()

    arr = np.clip(arr, lower, upper)
    arr = (arr - lower) / (upper - lower + 1e-10)
    arr = np.clip(arr * 255.0, 0, 255)

    if photometric == "MONOCHROME1":
        arr = 255.0 - arr

    return arr.astype(np.uint8)


def _normalize_rgb(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float64)
    lower = np.percentile(arr, 1)
    upper = np.percentile(arr, 99)
    if upper <= lower:
        lower = arr.min()
        upper = arr.max()
    arr = np.clip(arr, lower, upper)
    arr = (arr - lower) / (upper - lower + 1e-10)
    arr = np.clip(arr * 255.0, 0, 255)
    return arr.astype(np.uint8)

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

_MAX_ARCHIVE_SIZE_BYTES = 500 * 1024 * 1024
_MAX_EXTRACTED_SIZE_BYTES = 2 * 1024 * 1024 * 1024
_MAX_FILE_COUNT = 10000
_MAX_COMPRESSION_RATIO = 100


def safe_extract_zip(
    archive_path: str | Path,
    *,
    max_archive_size: int = _MAX_ARCHIVE_SIZE_BYTES,
    max_extracted_size: int = _MAX_EXTRACTED_SIZE_BYTES,
    max_file_count: int = _MAX_FILE_COUNT,
    max_compression_ratio: float = _MAX_COMPRESSION_RATIO,
) -> str:
    archive_path = Path(archive_path)
    archive_size = archive_path.stat().st_size
    if archive_size > max_archive_size:
        raise ValueError(
            f"Archive size ({archive_size} bytes) exceeds limit ({max_archive_size} bytes)"
        )

    extract_dir = tempfile.mkdtemp(prefix="radscan_zip_")
    extracted_size = 0
    file_count = 0

    with zipfile.ZipFile(archive_path, "r") as zf:
        for info in zf.infolist():
            file_count += 1
            if file_count > max_file_count:
                raise ValueError(
                    f"Archive contains more than {max_file_count} entries"
                )

            if info.is_dir():
                continue

            compressed_size = info.compress_size
            if compressed_size > 0:
                ratio = info.file_size / compressed_size
                if ratio > max_compression_ratio:
                    raise ValueError(
                        f"Compression ratio {ratio:.1f} exceeds limit "
                        f"({max_compression_ratio}) for entry {info.filename}"
                    )

            extracted_size += info.file_size
            if extracted_size > max_extracted_size:
                raise ValueError(
                    f"Extracted size exceeds limit ({max_extracted_size} bytes)"
                )

            dest = Path(extract_dir) / info.filename
            try:
                dest.resolve().relative_to(Path(extract_dir).resolve())
            except ValueError:
                raise ValueError(
                    f"Path traversal detected in archive entry: {info.filename}"
                )
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                zf.extract(info, extract_dir)
            except Exception as exc:
                raise ValueError(
                    f"Failed to extract {info.filename}: {exc}"
                ) from exc

    return extract_dir


def cleanup_temp_dir(temp_dir: str) -> None:
    import shutil

    if temp_dir and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

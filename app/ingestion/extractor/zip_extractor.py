import os
import shutil
import stat
from pathlib import Path
from zipfile import BadZipFile, ZipFile

MAX_ZIP_ENTRIES = 1000
MAX_EXTRACTED_FILE_SIZE = 100 * 1024 * 1024
MAX_TOTAL_EXTRACTED_SIZE = 500 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
EXTRACTION_CHUNK_SIZE = 1024 * 1024


class ZipExtractor:

    def extract(
        self,
        zip_path: Path,
        output_dir: Path,
    ) -> list[Path]:

        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        extracted_files = []
        total_extracted_size = 0
        seen_paths = set()

        try:
            with ZipFile(zip_path, "r") as archive:
                members = archive.infolist()

                if len(members) > MAX_ZIP_ENTRIES:
                    raise ValueError(
                        f"ZIP contains too many entries. "
                        f"Maximum allowed: {MAX_ZIP_ENTRIES}."
                    )

                for member in members:
                    if member.is_dir():
                        continue

                    if member.flag_bits & 0x1:
                        raise ValueError(
                            "Encrypted ZIP entries are not supported."
                        )

                    if member.file_size > MAX_EXTRACTED_FILE_SIZE:
                        raise ValueError(
                            f"ZIP entry exceeds the maximum file size: "
                            f"{member.filename}"
                        )

                    if member.file_size > 0:
                        if member.compress_size == 0:
                            raise ValueError(
                                "Invalid ZIP compression metadata."
                            )

                        ratio = member.file_size / member.compress_size

                        if ratio > MAX_COMPRESSION_RATIO:
                            raise ValueError(
                                f"ZIP entry has an excessive compression "
                                f"ratio: {member.filename}"
                            )

                    total_extracted_size += member.file_size

                    if total_extracted_size > MAX_TOTAL_EXTRACTED_SIZE:
                        raise ValueError(
                            "ZIP exceeds the maximum total extracted size."
                        )

                    if "\\" in member.filename or "\x00" in member.filename:
                        raise ValueError("Unsafe ZIP file path detected.")

                    raw_path = Path(member.filename)

                    if raw_path.is_absolute() or ".." in raw_path.parts:
                        raise ValueError(
                            "Unsafe ZIP file path detected."
                        )

                    if not raw_path.parts:
                        raise ValueError(
                            "Invalid ZIP entry path."
                        )

                    target_path = (
                        output_dir / raw_path
                    ).resolve()

                    if not target_path.is_relative_to(output_dir):   # checks actual path containment instead of string prefixes.
                        raise ValueError(
                            "Unsafe ZIP file path detected."
                        )

                    relative_path = target_path.relative_to(output_dir)

                    if relative_path in seen_paths:
                        raise ValueError(
                            f"Duplicate ZIP entry detected: "
                            f"{member.filename}"
                        )

                    seen_paths.add(relative_path)

                    unix_mode = member.external_attr >> 16

                    if stat.S_ISLNK(unix_mode):
                        raise ValueError(
                            "Symbolic links are not allowed in ZIP files."
                        )

                    target_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    written_size = 0

                    with archive.open(member, "r") as source:    # lets us extract incrementally rather than loading an entire entry into memory.
                        with target_path.open("wb") as target:
                            while chunk := source.read(
                                EXTRACTION_CHUNK_SIZE
                            ):
                                written_size += len(chunk)

                                if written_size > MAX_EXTRACTED_FILE_SIZE:
                                    raise ValueError(
                                        "Extracted file exceeded the "
                                        "maximum allowed size."
                                    )

                                if (
                                    total_extracted_size
                                    - member.file_size
                                    + written_size
                                    > MAX_TOTAL_EXTRACTED_SIZE
                                ):
                                    raise ValueError(
                                        "ZIP exceeded the maximum total "
                                        "extracted size."
                                    )

                                target.write(chunk)

                    if written_size != member.file_size:
                        raise ValueError(
                            f"ZIP entry size mismatch: {member.filename}"
                        )

                    extracted_files.append(target_path)

            return extracted_files

        except BadZipFile as exc:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise ValueError("Invalid or corrupted ZIP file.") from exc

        except Exception:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise

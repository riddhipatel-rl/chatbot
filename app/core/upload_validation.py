
import os
from pathlib import Path

from app.ingestion.detector import SUPPORTED_EXTENSIONS

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ZIP_SIGNATURES = (
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
)

OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

SIGNATURES = {
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}


def validate_upload(
    filename: str,
    size_bytes: int,
    header: bytes,
    *,
    allow_zip: bool = False,
) -> None:
    if not filename or not filename.strip():
        raise ValueError("Filename is required.")

    extension = Path(filename).suffix.lower()

    allowed = set(SUPPORTED_EXTENSIONS)
    if allow_zip:
        allowed.add(".zip")

    if extension not in allowed:
        raise ValueError(
            f"Unsupported file format: {extension or 'no extension'}."
        )

    if size_bytes == 0:
        raise ValueError("The uploaded file is empty.")

    if size_bytes > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"File exceeds the maximum upload size of "
            f"{MAX_UPLOAD_SIZE_MB} MB."
        )

    header = header[:16]

    if extension in SIGNATURES:
        if not any(
            header.startswith(signature)
            for signature in SIGNATURES[extension]
        ):
            raise ValueError(
                f"File content does not match the {extension} format."
            )

    elif extension in {".zip", ".docx", ".xlsx", ".pptx"}:
        if not header.startswith(ZIP_SIGNATURES):
            raise ValueError(
                f"File content does not match the {extension} format."
            )

    elif extension in {".doc", ".xls", ".ppt"}:
        if not header.startswith(OLE_SIGNATURE):
            raise ValueError(
                f"File content does not match the {extension} format."
            )

    elif b"\x00" in header:
        raise ValueError(
            "The uploaded file appears to contain binary data."
        )

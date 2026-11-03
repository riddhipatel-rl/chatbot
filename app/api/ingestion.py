
from pathlib import Path
from typing import Annotated
from uuid import uuid4
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.upload_validation import (
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
    validate_upload,
)
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger("chatbot")

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_CHUNK_SIZE = 1024 * 1024

ingestion_service = IngestionService()
retrieval_service = RetrievalService()


async def _save_validated_upload(
    file: UploadFile,
    *,
    allow_zip: bool,
) -> Path:
    file_path = None

    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required.",
            )

        extension = Path(file.filename).suffix.lower()

        allowed_extensions = {
            ".pdf", ".doc", ".docx", ".txt", ".md",
            ".xls", ".xlsx", ".csv", ".ppt", ".pptx",
            ".jpg", ".jpeg", ".png", ".html", ".htm",
            ".xml", ".json",
        }
        if allow_zip:
            allowed_extensions.add(".zip")

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format.",
            )

        file_path = UPLOAD_DIR / f"{uuid4()}{extension}"

        total_bytes = 0
        header = bytearray()

        with file_path.open("wb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                total_bytes += len(chunk)

                if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"File exceeds the maximum upload size "
                            f"of {MAX_UPLOAD_SIZE_MB} MB."
                        ),
                    )

                if len(header) < 16:
                    header.extend(chunk[:16 - len(header)])

                destination.write(chunk)

        validate_upload(
            filename=file.filename,
            size_bytes=total_bytes,
            header=bytes(header),
            allow_zip=allow_zip,
        )

        return file_path

    except ValueError as exc:
        if file_path is not None:
            file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        if file_path is not None:
            file_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    original_filename = file.filename

    file_path = await _save_validated_upload(
        file,
        allow_zip=False,
    )

    try:
        result = ingestion_service.ingest(
            file_path,
            original_filename=original_filename,
        )

        retrieval_service.refresh_index()

        return {
            "document_id": result["document_id"],
            "filename": original_filename,
            "chunks": len(result["chunks"]),
            "cached": result["cached"],
            "status": "processed",
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Document ingestion failed")

        raise HTTPException(
            status_code=500,
            detail="Document processing failed.",
        ) from exc

    finally:
        file_path.unlink(missing_ok=True)


@router.post("/upload-multiple")
async def upload_multiple(
    files: Annotated[list[UploadFile], File(...)],
):
    results = []

    try:
        for file in files:
            original_filename = file.filename

            file_path = await _save_validated_upload(
                file,
                allow_zip=True,
            )

            try:
                if file_path.suffix.lower() == ".zip":
                    zip_results = ingestion_service.ingest_zip(
                        file_path
                    )

                    for result in zip_results:
                        results.append({
                            "document_id": result["document_id"],
                            "filename": result["source_file"],
                            "file_hash": result["file_hash"],
                            "chunks": result["chunks"],
                            "cached": result["cached"],
                            "status": (
                                "reused"
                                if result["cached"]
                                else "processed"
                            ),
                        })

                else:
                    result = ingestion_service.ingest(
                        file_path,
                        original_filename=original_filename,
                    )

                    results.append({
                        "document_id": result["document_id"],
                        "filename": original_filename,
                        "file_hash": result["file_hash"],
                        "chunks": len(result["chunks"]),
                        "cached": result["cached"],
                        "status": (
                            "reused"
                            if result["cached"]
                            else "processed"
                        ),
                    })

            finally:
                file_path.unlink(missing_ok=True)

        retrieval_service.refresh_index()

        return {
            "total_files": len(results),
            "total_chunks": sum(
                result["chunks"]
                for result in results
            ),
            "index_refreshed": True,
            "documents": results,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Multiple document ingestion failed")

        raise HTTPException(
            status_code=500,
            detail="Document processing failed.",
        ) from exc

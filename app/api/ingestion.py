
from typing import Annotated
from pathlib import Path
from uuid import uuid4
import shutil
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import (
    RetrievalService,
)
from app.services.retrieval_service import retrieval_service

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ingestion_service = IngestionService()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    file_id = str(uuid4())

    extension = Path(
        file.filename
    ).suffix.lower()

    saved_filename = (
        f"{file_id}{extension}"
    )

    file_path = (
        UPLOAD_DIR / saved_filename
    )

    try:

        with file_path.open("wb") as buffer:

            while chunk := await file.read(
                1024 * 1024
            ):
                buffer.write(chunk)

        result = ingestion_service.ingest(
            file_path
        )
        retrieval_service.refresh_index()

        return {
            "document_id": result["document_id"],
            "filename": file.filename,
            "chunks": len(result["chunks"]),
            "cached": result["cached"],
            "status": "processed",
        }

    except ValueError as exc:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Document processing failed",
        )


@router.post("/upload-multiple")
async def upload_multiple(
    files: Annotated[list[UploadFile], File(...)]
):
    results = []

    for file in files:

        file_path = (
            UPLOAD_DIR
            / f"{uuid4()}{Path(file.filename).suffix}"
        )

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        if file.filename.lower().endswith(".zip"):

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
                original_filename=file.filename,
            )

            results.append({
                "document_id": result["document_id"],
                "filename": file.filename,
                "file_hash": result["file_hash"],
                "chunks": len(result["chunks"]),
                "cached": result["cached"],
                "status": (
                    "reused"
                    if result["cached"]
                    else "processed"
                ),
            })

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
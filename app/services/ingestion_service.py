from pathlib import Path

from app.ingestion.chunker import DocumentChunker
from app.ingestion.detector import is_supported
from app.ingestion.docling_converter import (
    DoclingConverter,
)
from app.ingestion.extractor.docling_extractor import DoclingExtractor
from app.storage.chunk_store import LocalChunkStore
from app.storage.file_store import calculate_file_hash
from app.ingestion.extractor.ocr_extractor import RapidOCRExtractor

from app.ingestion.pdf_ocr import PDFOCRProcessor
from uuid import uuid4

from app.ingestion.extractor.zip_extractor import ZipExtractor
from app.ingestion.extractor.xml_extractor import XMLExtractor
from app.ingestion.extractor.pdf_extractor import PDFExtractor
from app.ingestion.document_renderer import DocumentRenderer


class IngestionService:

    def __init__(self):

        self.converter = DoclingConverter()

        self.extractor = DoclingExtractor()

        self.chunker = DocumentChunker(
            max_tokens=600,
            overlap_tokens=100,
        )

        self.chunk_store = LocalChunkStore()
        self.ocr_extractor = RapidOCRExtractor()
        self.pdf_ocr = PDFOCRProcessor()
        self.zip_extractor = ZipExtractor()
        self.xml_extractor = XMLExtractor()
        self.pdf_extractor = PDFExtractor()
        self.document_renderer = DocumentRenderer()

    def ingest(
        self,
        file_path: Path,
        original_filename: str | None = None,
    ):
        source_file = original_filename or file_path.name

        if not is_supported(
            file_path.name
        ):
            raise ValueError(
                f"Unsupported file format: "
                f"{file_path.suffix}"
            )

        file_hash = calculate_file_hash(
            file_path
        )

        existing = self.chunk_store.find_by_hash(
            file_hash
        )

        if existing:

            document_id, chunks = existing

            return {
                "document_id": document_id,
                "source_file": file_path.name,
                "file_hash": file_hash,
                "chunks": chunks,
                "cached": True,
            }
        
        existing_document = self.chunk_store.find_by_source_file(
            source_file
        )
        document_id = None

        if existing_document:
            document_id, old_hash, _ = existing_document

            if old_hash != file_hash:
                self.chunk_store.delete(
                    document_id
                )

        extension = file_path.suffix.lower()

        if extension == ".pdf":

            canonical = self.pdf_extractor.extract(
                file_path,
                source_file=source_file,
                file_type=".pdf",
            )

            if not canonical.elements:

                searchable_path = (
                    Path("data/ocr") / file_path.name
                )

                self.pdf_ocr.make_searchable(
                    input_path=file_path,
                    output_path=searchable_path,
                )

                canonical = self.pdf_extractor.extract(
                    searchable_path,
                    source_file=source_file,
                    file_type=".pdf",
                )

        elif extension in {
            ".png",
            ".jpg",
            ".jpeg",
        }:

            canonical = self.ocr_extractor.extract(
                file_path
            )

        elif extension == ".xml":

            canonical = self.xml_extractor.extract(
                file_path
            )

        elif extension == ".docx":
            rendered_dir = Path("data/rendered")

            rendered_pdf = self.document_renderer.render_to_pdf(
                input_path=file_path,
                output_dir=rendered_dir,
            )

            canonical = self.pdf_extractor.extract(
                rendered_pdf,
                source_file=source_file,
                file_type=".docx",
            )

        else:

            document = self.converter.convert(
                file_path
            )

            canonical = self.extractor.extract(
                document,
                source_file=source_file,
            )

        chunks = self.chunker.chunk(
            canonical
        )
        print("DEBUG CANONICAL:", canonical.source_file)
        print(
            "DEBUG CHUNKS:",
            {chunk.source_file for chunk in chunks}
        )

        self.chunk_store.save(
            document_id=canonical.document_id,
            source_file=canonical.source_file,
            file_hash=file_hash,
            chunks=chunks,
        )

        return {
            "document_id": canonical.document_id,
            "source_file": canonical.source_file,
            "file_hash": file_hash,
            "chunks": chunks,
            "cached": False,
        }

    def ingest_zip(
        self,
        zip_path: Path,
    ):
        extract_dir = (
            Path("uploads")
            / f"zip_{uuid4()}"
        )

        extracted_files = self.zip_extractor.extract(
            zip_path,
            extract_dir,
        )

        results = []

        for file_path in extracted_files:

            if not is_supported(file_path.name):
                continue

            result = self.ingest(file_path)

            results.append({
                "document_id": result["document_id"],
                "source_file": file_path.name,
                "file_hash": result["file_hash"],
                "chunks": len(result["chunks"]),
                "cached": result["cached"],
            })

        return results
from pathlib import Path
import os

from dotenv import load_dotenv
from app.retrieval.embedding_service import EmbeddingService
from torch import chunk

from app.ingestion.chunker import DocumentChunker
from app.ingestion.detector import is_supported
from app.ingestion.docling_converter import (
    DoclingConverter,
)
from app.ingestion.extractor.docling_extractor import DoclingExtractor

from app.storage.file_store import calculate_file_hash
from app.ingestion.extractor.ocr_extractor import RapidOCRExtractor

from app.ingestion.pdf_ocr import PDFOCRProcessor
from uuid import uuid4

from app.ingestion.extractor.zip_extractor import ZipExtractor
from app.ingestion.extractor.xml_extractor import XMLExtractor
from app.ingestion.extractor.pdf_extractor import PDFExtractor
from app.ingestion.document_renderer import DocumentRenderer

from app.db.database import SessionLocal
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.chunk_repository import ChunkRepository
from app.ingestion.analyzer.page_analyzer import PDFPageAnalyzer
from app.ingestion.analyzer.page_router import PageRouter
from app.ingestion.models import DocumentChunk, SourceLocation

from app.ingestion.extractor.visual_metadata_extractor import (
    VisualMetadataExtractor,
)

from collections import Counter
class IngestionService:

    def __init__(self):

        self.converter = DoclingConverter()

        self.extractor = DoclingExtractor()

        self.chunker = DocumentChunker(
            max_tokens=600,
            overlap_tokens=100,
        )


        load_dotenv()

        self.db_enabled = bool(os.getenv("DATABASE_URL"))
        self.embedding_service = (
            EmbeddingService() if self.db_enabled else None
        )

        self.ocr_extractor = RapidOCRExtractor()
        self.pdf_ocr = PDFOCRProcessor()
        self.zip_extractor = ZipExtractor()
        self.xml_extractor = XMLExtractor()
        self.pdf_extractor = PDFExtractor()
        self.document_renderer = DocumentRenderer()
        self.page_analyzer = PDFPageAnalyzer()
        self.page_router = PageRouter()
        self.visual_metadata_extractor = VisualMetadataExtractor()

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
       

        version_state = self._get_version_state(
            source_file=source_file,
            file_hash=file_hash,
        )

        matching = version_state["matching"]

        if matching is not None:
            document_id = matching["document_id"]
            extension = file_path.suffix.lower()

            render_path = None

            if extension == ".pdf":
                render_path = file_path.resolve()

            elif extension in {".docx", ".pptx"}:
                rendered_dir = (
                    Path("data/rendered")
                    / document_id
                )

                rendered_pdf_path = (
                    rendered_dir
                    / f"{file_path.stem}.pdf"
                )

                if rendered_pdf_path.exists():
                    rendered_pdf_path.unlink()

                rendered_pdf = (
                    self.document_renderer.render_to_pdf(
                        input_path=file_path,
                        output_dir=rendered_dir,
                    )
                )

                render_path = rendered_pdf.resolve()

            elif extension in {".png", ".jpg", ".jpeg"}:
                render_path = file_path.resolve()

            with SessionLocal.begin() as session:
                repository = ChunkRepository(session)

                repository.update_document_file_paths(
                    document_id=document_id,
                    file_path=str(file_path.resolve()),
                    file_type=extension,
                    render_path=(
                        str(render_path)
                        if render_path
                        else None
                    ),
                )

            chunks = self._load_postgres_chunks(
                document_id=document_id,
                source_file=matching["source_file"],
            )

            return {
                "document_id": document_id,
                "source_file": matching["source_file"],
                "file_hash": file_hash,
                "logical_document_id": matching[
                    "logical_document_id"
                ],
                "version_number": matching["version_number"],
                "chunks": chunks,
                "cached": True,
            }

        latest = version_state["latest"]

        logical_document_id = (
            latest["logical_document_id"]
            if latest is not None
            else None
        )

        version_number = (
            version_state["next_version_number"]
            if latest is not None
            else 1
        )

        
        document_id = None


        extension = file_path.suffix.lower()
        render_path = None

        if extension == ".pdf":

            render_path = file_path

            analyses = self.page_analyzer.analyze(file_path)

            visual_pages = {
                analysis.page_number
                for analysis in analyses
                if analysis.is_visual_heavy
            }

            normal_pages = {
                analysis.page_number
                for analysis in analyses
                if not analysis.is_visual_heavy
            }

            print("========== PDF PAGE ROUTING ==========")
            print("Normal pages:", sorted(normal_pages))
            print("Visual pages:", sorted(visual_pages))
            print("======================================")

            canonical = self.pdf_extractor.extract(
                file_path,
                source_file=source_file,
                file_type=".pdf",
                page_numbers=normal_pages,
            )

            visual_elements = self.visual_metadata_extractor.extract(
                file_path,
                page_numbers=visual_pages,
            )

            canonical.elements.extend(visual_elements)

            canonical.elements.sort(
                key=lambda element: (
                    element.location.page or 0,
                    element.order,
                )
            )

            for order, element in enumerate(canonical.elements):
                element.order = order

        elif extension == ".pptx":

            rendered_dir = Path("data/rendered")

            rendered_pdf = self.document_renderer.render_to_pdf(
                input_path=file_path,
                output_dir=rendered_dir,
            )

            render_path = rendered_pdf

            analyses = self.page_analyzer.analyze(
                rendered_pdf
            )

            visual_pages = {
                analysis.page_number
                for analysis in analyses
                if analysis.is_visual_heavy
            }

            normal_pages = {
                analysis.page_number
                for analysis in analyses
                if not analysis.is_visual_heavy
            }

            print("========== PPTX PAGE ROUTING ==========")
            print("Normal slides:", sorted(normal_pages))
            print("Visual slides:", sorted(visual_pages))
            print("=======================================")

            document = self.converter.convert(
                file_path
            )

            canonical = self.extractor.extract(
                document,
                source_file=source_file,
            )

            visual_elements = self.visual_metadata_extractor.extract(
                rendered_pdf,
                page_numbers=visual_pages,
            )

            canonical.elements.extend(
                visual_elements
            )

            canonical.elements.sort(
                key=lambda element: (
                    element.location.page or 0,
                    element.order,
                )
            )

            for order, element in enumerate(
                canonical.elements
            ):
                element.order = order

        elif extension in {
            ".png",
            ".jpg",
            ".jpeg",
        }:
            render_path = file_path

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

        for chunk in chunks:
            chunk.metadata["file_path"] = str(file_path)
            chunk.metadata["file_type"] = extension

            if render_path:
                chunk.metadata["render_path"] = str(render_path)

            if extension == ".pdf":
                chunk.metadata["render_path"] = str(file_path)

            elif extension == ".docx":
                chunk.metadata["render_path"] = str(rendered_pdf)

        print("DEBUG CANONICAL:", canonical.source_file)
        print(
            "DEBUG CHUNKS:",
            {chunk.source_file for chunk in chunks}
        )
        print("========== CHUNK METADATA BEFORE SAVE ==========")

        for chunk in chunks[:2]:
            print(chunk.metadata)

        print("===============================================")

        if logical_document_id is None:
            logical_document_id = canonical.document_id

        if self.db_enabled:
            self._persist_to_postgres(
                document_id=canonical.document_id,
                logical_document_id=logical_document_id,
                version_number=version_number,
                source_file=canonical.source_file,
                file_type=extension,
                file_hash=file_hash,
                chunks=chunks,
            )


        return {
            "document_id": canonical.document_id,
            "source_file": canonical.source_file,
            "file_hash": file_hash,
            "logical_document_id": logical_document_id,
            "version_number": version_number,
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

    def _persist_to_postgres(
        self,
        document_id: str,
        logical_document_id: str,
        version_number: int,
        source_file: str,
        file_type: str,
        file_hash: str,
        chunks: list,
    ):
        if not self.db_enabled:
            return

        embeddings = (
            self.embedding_service.embed(
                [chunk.text for chunk in chunks]
            )
            if chunks
            else []
        )

        with SessionLocal.begin() as session:
            document_repository = DocumentRepository(session)
            chunk_repository = ChunkRepository(session)

            document_repository.mark_versions_not_latest(
                logical_document_id=logical_document_id,
            )

            document_repository.create(
                document_id=document_id,
                source_file=source_file,
                file_type=file_type,
                file_hash=file_hash,
                logical_document_id=logical_document_id,
                version_number=version_number,
                is_latest=True,
            )

            for chunk, embedding in zip(chunks, embeddings):
                chunk_repository.create(
                    chunk=chunk,
                    embedding=embedding.tolist(),
                )

    def _get_version_state(
        self,
        source_file: str,
        file_hash: str,
    ) -> dict:
        if not self.db_enabled:
            return {
                "latest": None,
                "matching": None,
                "next_version_number": 1,
            }

        with SessionLocal.begin() as session:
            repository = DocumentRepository(session)

            latest = repository.get_by_source_file(source_file)

            if latest is None:
                return {
                    "latest": None,
                    "matching": None,
                    "next_version_number": 1,
                }

            logical_document_id = latest.logical_document_id

            latest_state = {
                "document_id": latest.id,
                "source_file": latest.source_file,
                "file_type": latest.file_type,
                "file_hash": latest.file_hash,
                "logical_document_id": logical_document_id,
                "version_number": latest.version_number,
            }

            matching = repository.get_by_hash_for_logical_document(
                logical_document_id=logical_document_id,
                file_hash=file_hash,
            )

            matching_state = None

            if matching is not None:
                matching_state = {
                    "document_id": matching.id,
                    "source_file": matching.source_file,
                    "file_type": matching.file_type,
                    "file_hash": matching.file_hash,
                    "logical_document_id": logical_document_id,
                    "version_number": matching.version_number,
                }

                repository.activate_version(
                    logical_document_id=logical_document_id,
                    document_id=matching.id,
                )

            return {
                "latest": latest_state,
                "matching": matching_state,
                "next_version_number": (
                    repository.get_next_version_number(logical_document_id)
                ),
            }

    def _load_postgres_chunks(
        self,
        document_id: str,
        source_file: str,
    ) -> list[DocumentChunk]:
        with SessionLocal() as session:
            repository = ChunkRepository(session)

            stored_chunks = repository.get_by_document_id(document_id)

            chunks = []

            for stored in stored_chunks:
                locations = [
                    SourceLocation(**location)
                    if isinstance(location, dict)
                    else location
                    for location in (stored.locations or [])
                ]

                chunks.append(
                    DocumentChunk(
                        chunk_id=stored.id,
                        document_id=stored.document_id,
                        text=stored.text,
                        source_file=source_file,
                        locations=locations,
                        element_types=stored.element_types or [],
                        metadata=stored.metadata_ or {},
                    )
                )

            return chunks
from pathlib import Path
from uuid import uuid4

import fitz

from app.ingestion.models import (
    CanonicalDocument,
    DocumentElement,
    SourceLocation,
)
from app.ingestion.extractor.ocr_extractor import RapidOCRExtractor


class ScannedPDFExtractor:

    def __init__(self):
        self.ocr_extractor = RapidOCRExtractor()

    def is_scanned(
        self,
        file_path: Path,
    ) -> bool:

        pdf = fitz.open(file_path)

        try:
            for page in pdf:
                if page.get_text().strip():
                    return False

            return True

        finally:
            pdf.close()

    def extract(
        self,
        file_path: Path,
    ) -> CanonicalDocument:

        document_id = str(uuid4())
        elements = []
        order = 0

        pdf = fitz.open(file_path)

        try:
            for page_number, page in enumerate(
                pdf,
                start=1,
            ):
                pixmap = page.get_pixmap(
                    dpi=150
                )

                image_bytes = pixmap.tobytes(
                    "png"
                )

                document = (
                    self.ocr_extractor.extract_image(
                        image_bytes,
                        source_file=file_path.name,
                        file_type=".pdf",
                    )
                )

                for element in document.elements:
                    element.order = order
                    element.location.page = page_number
                    element.metadata["document_id"] = document_id

                    elements.append(element)

                    order += 1

        finally:
            pdf.close()

        return CanonicalDocument(
            document_id=document_id,
            source_file=file_path.name,
            file_type=".pdf",
            elements=elements,
        )
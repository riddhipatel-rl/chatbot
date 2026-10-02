from pathlib import Path
from uuid import uuid4

import pymupdf

from app.ingestion.models import (
    CanonicalDocument,
    DocumentElement,
    SourceLocation,
)
from app.ingestion.text_normalizer import TextNormalizer


class PDFExtractor:
    def __init__(self):
        self.normalizer = TextNormalizer()

    def extract(
        self,
        file_path: Path,
        source_file: str | None = None,
        file_type: str | None = None,
        page_numbers: set[int] | None = None,
    ) -> CanonicalDocument:

        source_file = source_file or file_path.name
        file_type = file_type or file_path.suffix.lower()
        document_id = str(uuid4())

        elements = []
        order = 0

        document = pymupdf.open(file_path)

        try:
            for page_number, page in enumerate(document, start=1):

                if page_numbers is not None and page_number not in page_numbers:
                    continue

                page_elements, order = self.extract_page(
                    page=page,
                    page_number=page_number,
                    source_file=source_file,
                    document_id=document_id,
                    start_order=order,
                )

                elements.extend(page_elements)

        finally:
            document.close()

        return CanonicalDocument(
            document_id=document_id,
            source_file=source_file,
            file_type=file_type,
            elements=elements,
        )

    def extract_page(
        self,
        page,
        page_number: int,
        source_file: str,
        document_id: str,
        start_order: int = 0,
    ):
        elements = []
        order = start_order

        blocks = page.get_text("blocks")

        for block in blocks:
            x0, y0, x1, y1, text, *_ = block

            text = self.normalizer.normalize(text)

            if not text:
                continue

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    text=text,
                    element_type="text",
                    source_file=source_file,
                    order=order,
                    location=SourceLocation(
                        page=page_number,
                        bbox={
                            "x0": x0,
                            "y0": y0,
                            "x1": x1,
                            "y1": y1,
                        },
                    ),
                    metadata={
                        "document_id": document_id,
                        "parser": "pymupdf",
                        "requires_vision": False,
                    },
                )
            )

            order += 1

        return elements, order
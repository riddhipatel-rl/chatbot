from pathlib import Path
from uuid import uuid4

import fitz

from app.ingestion.base import DocumentParser
from app.ingestion.models import (
    Document,
    DocumentElement,
    SourceLocation,
)


class PDFParser(DocumentParser):

    def parse(self, file_path: Path) -> Document:
        document_id = str(uuid4())

        pdf = fitz.open(file_path)

        elements = []

        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            if not text:
                continue

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    element_type="text",
                    text=text,
                    location=SourceLocation(
                        page=page_number
                    ),
                )
            )

        pdf.close()

        return Document(
            document_id=document_id,
            file_name=file_path.name,
            file_type="pdf",
            elements=elements,
        )
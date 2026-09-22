from pathlib import Path
from uuid import uuid4

import fitz

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
    ) -> CanonicalDocument:
        source_file = source_file or file_path.name
        file_type = file_type or file_path.suffix.lower()

        document_id = str(uuid4())
        elements = []
        order = 0

        doc = fitz.open(file_path)

        for page_no, page in enumerate(doc):

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
                            page=page_no + 1,
                            bbox={
                                "left": x0,
                                "top": y0,
                                "right": x1,
                                "bottom": y1,
                            },
                        ),
                        metadata={
                            "document_id": document_id,
                            "parser": "pymupdf",
                        },
                    )
                )

                order += 1

        doc.close()

        return CanonicalDocument(
            document_id=document_id,
            source_file=source_file,
            file_type=file_type,
            elements=elements,
        )
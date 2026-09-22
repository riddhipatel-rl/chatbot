from pathlib import Path
from uuid import uuid4

from PIL import Image
import pytesseract

from app.ingestion.base import DocumentParser
from app.ingestion.models import Document, DocumentElement


class ImageParser(DocumentParser):

    def parse(self, file_path: Path) -> Document:
        document_id = str(uuid4())

        image = Image.open(file_path)

        text = pytesseract.image_to_string(image).strip()

        elements = []

        if text:
            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    element_type="ocr_text",
                    text=text,
                    metadata={
                        "ocr": True,
                    },
                )
            )

        return Document(
            document_id=document_id,
            file_name=file_path.name,
            file_type=file_path.suffix.lower().lstrip("."),
            elements=elements,
        )
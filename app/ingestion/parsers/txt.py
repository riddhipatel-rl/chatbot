from pathlib import Path
from uuid import uuid4

from app.ingestion.base import DocumentParser
from app.ingestion.models import (
    Document,
    DocumentElement,
    SourceLocation,
)


class TXTParser(DocumentParser):

    def parse(self, file_path: Path) -> Document:
        document_id = str(uuid4())

        text = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        elements = []

        for line_number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    element_type="text",
                    text=line,
                    location=SourceLocation(
                        line_start=line_number,
                        line_end=line_number,
                    ),
                )
            )

        return Document(
            document_id=document_id,
            file_name=file_path.name,
            file_type="txt",
            elements=elements,
        )
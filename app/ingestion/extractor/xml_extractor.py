from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET

from app.ingestion.models import (
    CanonicalDocument,
    DocumentElement,
    SourceLocation,
)
from app.ingestion.text_normalizer import TextNormalizer


class XMLExtractor:

    def __init__(self):
        self.normalizer = TextNormalizer()

    def extract(
        self,
        file_path: Path,
    ) -> CanonicalDocument:

        document_id = str(uuid4())

        tree = ET.parse(file_path)
        root = tree.getroot()

        elements = []
        order = 0

        for element in root.iter():

            text_parts = []

            if element.text:
                text_parts.append(
                    element.text.strip()
                )

            for child in element:
                if child.tail:
                    text_parts.append(
                        child.tail.strip()
                    )

            text = " ".join(
                part
                for part in text_parts
                if part
            )

            text = self.normalizer.normalize(
                text
            )

            if not text:
                continue

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    text=text,
                    element_type="xml_element",
                    source_file=file_path.name,
                    order=order,
                    location=SourceLocation(),
                    metadata={
                        "document_id": document_id,
                        "xml_tag": element.tag,
                        "xml_attributes": element.attrib,
                    },
                )
            )

            order += 1

        return CanonicalDocument(
            document_id=document_id,
            source_file=file_path.name,
            file_type=".xml",
            elements=elements,
        )
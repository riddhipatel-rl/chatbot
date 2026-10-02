import re
from uuid import uuid4

from app.ingestion.models import (
    CanonicalDocument,
    DocumentChunk,
    DocumentElement,
)


class DocumentChunker:

    def __init__(
        self,
        max_tokens: int = 600,
        overlap_tokens: int = 100,
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk(
        self,
        document: CanonicalDocument,
    ) -> list[DocumentChunk]:

        elements = sorted(
            document.elements,
            key=lambda element: element.order,
        )

        chunks = []
        current_elements = []
        current_tokens = 0
        current_page = None

        for element in elements:

            element_page = (
                element.location.page
                if element.location
                else None
            )

            element_tokens = self._estimate_tokens(
                element.text
            )

            if current_page is None:
                current_page = element_page

            if (
                current_elements
                and element_page != current_page
            ):
                chunks.append(
                    self._create_chunk(
                        current_elements,
                        document.source_file
                    )
                )

                current_elements = []
                current_tokens = 0
                current_page = element_page

            if self._is_heading(element):

                if current_elements:
                    chunks.append(
                        self._create_chunk(
                            current_elements,
                            document.source_file,
                        )
                    )

                    current_elements = []
                    current_tokens = 0

            if (
                current_elements
                and current_tokens + element_tokens
                > self.max_tokens
            ):
                chunks.append(
                    self._create_chunk(
                        current_elements,
                        document.source_file,
                    )
                )

                current_elements = self._get_overlap(
                    current_elements,
                    current_page,
                )

                current_tokens = sum(
                    self._estimate_tokens(
                        item.text
                    )
                    for item in current_elements
                )

            current_elements.append(element)
            current_tokens += element_tokens

        if current_elements:
            chunks.append(
                self._create_chunk(
                    current_elements,
                    document.source_file,
                )
            )

        return chunks

    def _create_chunk(
        self,
        elements: list[DocumentElement],
        source_file: str,
    ) -> DocumentChunk:

        text = "\n".join(
            element.text
            for element in elements
        )

        document_id = elements[0].metadata.get(
            "document_id"
        )

        visual_metadata = []

        for element in elements:

            if element.element_type.lower() != "visual":
                continue

            metadata = element.metadata

            visual_metadata.append(
                {
                    "element_id": element.element_id,
                    "page": (
                        element.location.page
                        if element.location
                        else None
                    ),
                    "title": metadata.get(
                        "visual_title"
                    ),
                    "text": element.text,
                    "parser": metadata.get(
                        "parser"
                    ),
                    "extractable": metadata.get(
                        "extractable"
                    ),
                    "ocr_required": metadata.get(
                        "ocr_required"
                    ),
                }
            )

        visual_page = any(
            element.metadata.get(
                "visual_page",
                False,
            )
            for element in elements
        )

        chunk_metadata = {
            "start_order": elements[0].order,
            "end_order": elements[-1].order,
            "element_count": len(elements),
            "visual_page": visual_page,
        }

        if visual_metadata:
            chunk_metadata[
                "visual_elements"
            ] = visual_metadata

        return DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=document_id,
            text=text,
            source_file=source_file,
            locations=[
                element.location
                for element in elements
            ],
            element_types=[
                element.element_type
                for element in elements
            ],
            metadata=chunk_metadata,
        )

    def _get_overlap(
        self,
        elements: list[DocumentElement],
        page: int | None,
    ) -> list[DocumentElement]:

        overlap = []
        tokens = 0

        for element in reversed(elements):

            element_page = (
                element.location.page
                if element.location
                else None
            )

            if element_page != page:
                break

            element_tokens = self._estimate_tokens(
                element.text
            )

            if tokens + element_tokens > self.overlap_tokens:
                break

            overlap.insert(0, element)
            tokens += element_tokens

        return overlap

    @staticmethod
    def _estimate_tokens(text: str) -> int:

        return max(
            1,
            len(
                re.findall(
                    r"\w+|[^\w\s]",
                    text,
                )
            )
            // 1,
        )

    @staticmethod
    def _is_heading(
        element: DocumentElement,
    ) -> bool:

        return element.element_type.lower() in {
            "title",
            "section_header",
            "heading",
        }
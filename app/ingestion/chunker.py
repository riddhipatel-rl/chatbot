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

        for element in elements:

            element_tokens = self._estimate_tokens(
                element.text
            )

            if self._is_heading(element):

                if current_elements:
                    chunks.append(
                        self._create_chunk(
                            current_elements
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
                        current_elements
                    )
                )

                current_elements = self._get_overlap(
                    current_elements
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
                    current_elements
                )
            )

        return chunks

    def _create_chunk(
        self,
        elements: list[DocumentElement],
    ) -> DocumentChunk:

        text = "\n".join(
            element.text
            for element in elements
        )

        document_id = elements[0].metadata.get(
            "document_id"
        )

        return DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=document_id,
            text=text,
            source_file=elements[0].source_file,
            locations=[
                element.location
                for element in elements
            ],
            element_types=[
                element.element_type
                for element in elements
            ],
            metadata={
                "start_order": elements[0].order,
                "end_order": elements[-1].order,
                "element_count": len(elements),
            },
        )

    def _get_overlap(
        self,
        elements: list[DocumentElement],
    ) -> list[DocumentElement]:

        overlap = []
        tokens = 0

        for element in reversed(elements):

            element_tokens = self._estimate_tokens(
                element.text
            )

            if (
                tokens + element_tokens
                > self.overlap_tokens
            ):
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
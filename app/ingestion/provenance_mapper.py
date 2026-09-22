from difflib import SequenceMatcher

from app.ingestion.models import (
    CanonicalDocument,
    DocumentElement,
    SourceLocation,
)


class ProvenanceMapper:

    def map_locations(
        self,
        canonical: CanonicalDocument,
        rendered_pdf: CanonicalDocument,
    ) -> CanonicalDocument:

        pdf_elements = rendered_pdf.elements

        for element in canonical.elements:

            if element.location.page is not None:
                continue

            match = self._find_best_match(
                element,
                pdf_elements,
            )

            if match is None:
                continue

            element.location = SourceLocation(
                page=match.location.page,
                bbox=match.location.bbox,
            )

            element.metadata["provenance_source"] = (
                "rendered_pdf"
            )

        return canonical

    def _find_best_match(
        self,
        element: DocumentElement,
        pdf_elements: list[DocumentElement],
    ) -> DocumentElement | None:

        source_text = self._normalize(
            element.text
        )

        if not source_text:
            return None

        best_match = None
        best_score = 0.0

        for pdf_element in pdf_elements:

            target_text = self._normalize(
                pdf_element.text
            )

            if not target_text:
                continue

            score = self._similarity(
                source_text,
                target_text,
            )

            if score > best_score:
                best_score = score
                best_match = pdf_element

        if best_score < 0.75:
            return None

        return best_match

    @staticmethod
    def _normalize(text: str) -> str:

        return " ".join(
            text.lower().split()
        )

    @staticmethod
    def _similarity(
        source: str,
        target: str,
    ) -> float:

        return SequenceMatcher(
            None,
            source,
            target,
        ).ratio()
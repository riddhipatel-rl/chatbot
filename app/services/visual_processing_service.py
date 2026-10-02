import re
from pathlib import Path

from app.ingestion.analyzer.page_analyzer import PDFPageAnalyzer
from app.ingestion.analyzer.page_renderer import PDFPageRenderer
from app.ingestion.extractor.vision_extractor import VisionExtractor
from app.ingestion.models import DocumentChunk


class VisualProcessingService:

    def __init__(self):
        self.page_analyzer = PDFPageAnalyzer()
        self.renderer = PDFPageRenderer()
        self.vision_extractor = VisionExtractor()

    def process_chunk(
        self,
        chunk: DocumentChunk,
        query: str,
    ) -> list[dict]:

        print("\n========== VISUAL PROCESSING ==========")
        print("Chunk:", chunk.chunk_id)
        print("Query:", query)

        render_path = chunk.metadata.get("render_path")

        if not render_path:
            print("❌ No render_path")
            return []

        pages = sorted(
            {
                location.page
                for location in chunk.locations
                if location.page
            }
        )

        print("Retrieved pages:", pages)

        if not pages:
            print("❌ No pages")
            return []

        text_evidence = self._build_text_evidence(chunk)

        print(
            "Text/OCR evidence length:",
            len(text_evidence),
        )

        if self._is_text_sufficient(
            query=query,
            text=text_evidence,
        ):
            print(
                "✅ Text/OCR evidence is sufficient."
            )
            print("⏭️ Skipping Qwen Vision.")
            print("=======================================\n")
            return []

        print(
            "⚠️ Text/OCR evidence is insufficient."
        )
        print(
            "Checking retrieved pages for visual processing..."
        )

        analyses = self.page_analyzer.analyze(
            Path(render_path)
        )

        visual_pages = {
            analysis.page_number
            for analysis in analyses
            if analysis.is_visual_heavy
        }

        print("Visual pages:", visual_pages)

        evidence = []

        for page_number in pages[:1]:

            if page_number not in visual_pages:
                print(
                    f"❌ Page {page_number} "
                    "is not visual-heavy"
                )
                continue

            print(
                f"✅ Processing visual page {page_number}"
            )

            image_path = self.renderer.render(
                file_path=Path(render_path),
                page_number=page_number,
                output_dir=Path(
                    "data/visual_pages"
                ),
            )

            print("Rendered:", image_path)

            vision_result = self.vision_extractor.extract(
                image_path=image_path,
                query=query,
                page_number=page_number,
            )

            print(
                "✅ Vision extraction completed"
            )

            evidence.append(
                {
                    "page": page_number,
                    "image_path": str(image_path),
                    "visual_result": vision_result,
                }
            )

        print(
            "Visual evidence count:",
            len(evidence),
        )

        print(
            "=======================================\n"
        )

        return evidence

    def _build_text_evidence(
        self,
        chunk: DocumentChunk,
    ) -> str:

        return " ".join(
            part
            for part in [
                chunk.text,
                *[
                    str(value)
                    for value in chunk.metadata.values()
                    if isinstance(value, str)
                ],
            ]
            if part
        )

    def _is_text_sufficient(
        self,
        query: str,
        text: str,
    ) -> bool:

        query_tokens = self._content_tokens(query)
        text_tokens = self._content_tokens(text)

        if not query_tokens or not text_tokens:
            return False

        overlap = query_tokens & text_tokens

        coverage = (
            len(overlap) / len(query_tokens)
        )

        print(
            "Query content tokens:",
            sorted(query_tokens),
        )

        print(
            "Matched tokens:",
            sorted(overlap),
        )

        print(
            "Text evidence coverage:",
            round(coverage, 2),
        )

        # Numeric questions need the requested
        # number/unit to survive retrieval.
        query_numbers = set(
            re.findall(
                r"\b\d+(?:\.\d+)?%?\b",
                query.lower(),
            )
        )

        if query_numbers:
            text_numbers = set(
                re.findall(
                    r"\b\d+(?:\.\d+)?%?\b",
                    text.lower(),
                )
            )

            if query_numbers & text_numbers:
                return True

            return False

        # For normal questions, require meaningful
        # lexical coverage from the retrieved text.
        return coverage >= 0.50

    @staticmethod
    def _content_tokens(text: str) -> set[str]:

        stop_words = {
            "what",
            "which",
            "where",
            "when",
            "who",
            "whom",
            "why",
            "how",
            "does",
            "do",
            "did",
            "is",
            "are",
            "was",
            "were",
            "the",
            "a",
            "an",
            "of",
            "to",
            "in",
            "on",
            "for",
            "from",
            "and",
            "or",
            "with",
            "by",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "represent",
            "mean",
        }

        tokens = re.findall(
            r"\b[a-zA-Z0-9][a-zA-Z0-9_-]*\b",
            text.lower(),
        )

        return {
            token
            for token in tokens
            if token not in stop_words
            and len(token) > 1
        }
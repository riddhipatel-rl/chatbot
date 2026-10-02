from pathlib import Path

import pymupdf

from app.ingestion.models import DocumentElement, SourceLocation
from app.ingestion.analyzer.page_analyzer import PDFPageAnalyzer
from app.ingestion.extractor.ocr_extractor import RapidOCRExtractor


class VisualMetadataExtractor:

    def __init__(self):
        self.page_analyzer = PDFPageAnalyzer()
        self.ocr = RapidOCRExtractor()

    def extract(
        self,
        file_path: Path,
        page_numbers: set[int] | None = None,
    ) -> list[DocumentElement]:

        analyses = self.page_analyzer.analyze(file_path)

        if page_numbers is not None:
            analyses = [
                analysis
                for analysis in analyses
                if analysis.page_number in page_numbers
            ]

        elements = []

        document = pymupdf.open(file_path)

        try:
            order = 0

            for analysis in analyses:

                if not analysis.is_visual_heavy:
                    continue

                page = document[analysis.page_number - 1]

                blocks = page.get_text("dict").get("blocks", [])

                native_text_blocks = []
                visual_blocks = []

                for block in blocks:

                    bbox = block.get("bbox")

                    if not bbox:
                        continue

                    if block.get("type") == 0:
                        text = self._extract_block_text(block)

                        if text:
                            native_text_blocks.append(
                                {
                                    "text": text,
                                    "bbox": bbox,
                                }
                            )

                    elif block.get("type") == 1:
                        visual_blocks.append(
                            {
                                "bbox": bbox,
                                "type": "image",
                            }
                        )

                for item in native_text_blocks:

                    x0, y0, x1, y1 = item["bbox"]

                    elements.append(
                        DocumentElement(
                            element_id=(
                                f"{file_path.stem}_"
                                f"page_{analysis.page_number}_"
                                f"text_{order}"
                            ),
                            text=item["text"],
                            element_type="text",
                            source_file=file_path.name,
                            order=order,
                            location=SourceLocation(
                                page=analysis.page_number,
                                bbox={
                                    "left": x0,
                                    "top": y0,
                                    "right": x1,
                                    "bottom": y1,
                                },
                            ),
                            metadata={
                                "parser": "pymupdf",
                                "extractable": True,
                                "visual_page": True,
                            },
                        )
                    )

                    order += 1

                for index, visual in enumerate(visual_blocks):

                    bbox = visual["bbox"]

                    ocr_text = self._ocr_region(
                        page,
                        bbox,
                    )

                    if not ocr_text:
                        continue

                    x0, y0, x1, y1 = bbox

                    elements.append(
                        DocumentElement(
                            element_id=(
                                f"{file_path.stem}_"
                                f"page_{analysis.page_number}_"
                                f"visual_{index}"
                            ),
                            text=ocr_text,
                            element_type="visual",
                            source_file=file_path.name,
                            order=order,
                            location=SourceLocation(
                                page=analysis.page_number,
                                bbox={
                                    "left": x0,
                                    "top": y0,
                                    "right": x1,
                                    "bottom": y1,
                                },
                            ),
                            metadata={
                                "parser": "rapidocr",
                                "extractable": False,
                                "ocr_required": True,
                                "visual_page": True,
                            },
                        )
                    )

                    order += 1

        finally:
            document.close()

        return elements

    def _extract_block_text(self, block: dict) -> str:

        parts = []

        for line in block.get("lines", []):

            for span in line.get("spans", []):

                text = span.get("text", "").strip()

                if text:
                    parts.append(text)

        return " ".join(parts).strip()

    def _ocr_region(self, page, bbox) -> str:

        rect = pymupdf.Rect(bbox)

        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2),
            clip=rect,
            alpha=False,
        )

        image = pixmap.tobytes("png")

        result = self.ocr.extract_image(
            image,
            source_file="visual_region",
        )

        if not result:
            return ""

        return " ".join(
            element.text
            for element in result.elements
            if element.text
        )
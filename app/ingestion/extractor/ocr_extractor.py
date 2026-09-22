from pathlib import Path
from uuid import uuid4

from rapidocr_onnxruntime import RapidOCR

from app.ingestion.models import (
    CanonicalDocument,
    DocumentElement,
    SourceLocation,
)
from app.ingestion.text_normalizer import TextNormalizer


class RapidOCRExtractor:

    def __init__(self):
        self.ocr = RapidOCR()
        self.normalizer = TextNormalizer()

    def extract(
        self,
        file_path: Path,
    ) -> CanonicalDocument:

        result, _ = self.ocr(
            str(file_path)
        )

        return self._build_document(
            result=result,
            source_file=file_path.name,
            file_type=file_path.suffix.lower(),
        )

    def extract_image(
        self,
        image,
        source_file: str,
        file_type: str = ".png",
    ) -> CanonicalDocument:

        result, _ = self.ocr(image)

        return self._build_document(
            result=result,
            source_file=source_file,
            file_type=file_type,
        )

    def _build_document(
        self,
        result,
        source_file: str,
        file_type: str,
    ) -> CanonicalDocument:

        document_id = str(uuid4())
        elements = []

        if not result:
            return CanonicalDocument(
                document_id=document_id,
                source_file=source_file,
                file_type=file_type,
                elements=[],
            )

        ocr_items = []

        for item in result:

            points = item[0]

            text = self.normalizer.normalize(
                item[1]
            )

            if not text:
                continue

            ocr_items.append({
                "text": text,
                "left": min(
                    point[0]
                    for point in points
                ),
                "top": min(
                    point[1]
                    for point in points
                ),
                "right": max(
                    point[0]
                    for point in points
                ),
                "bottom": max(
                    point[1]
                    for point in points
                ),
                "confidence": float(item[2]),
            })

        ocr_items = self._group_lines(
            ocr_items
        )

        for order, item in enumerate(
            ocr_items
        ):

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    text=item["text"],
                    element_type="text",
                    source_file=source_file,
                    order=order,
                    location=SourceLocation(
                        bbox={
                            "left": item["left"],
                            "bottom": item["bottom"],
                            "right": item["right"],
                            "top": item["top"],
                        }
                    ),
                    metadata={
                        "document_id": document_id,
                        "ocr": True,
                        "confidence": item["confidence"],
                    },
                )
            )

        return CanonicalDocument(
            document_id=document_id,
            source_file=source_file,
            file_type=file_type,
            elements=elements,
        )

    def _group_lines(self, items):

        items = sorted(
            items,
            key=lambda item: item["top"],
        )

        lines = []

        for item in items:

            item_height = (
                item["bottom"]
                - item["top"]
            )

            placed = False

            for line in lines:

                line_top = min(
                    x["top"]
                    for x in line
                )

                line_bottom = max(
                    x["bottom"]
                    for x in line
                )

                line_height = (
                    line_bottom
                    - line_top
                )

                tolerance = max(
                    item_height,
                    line_height,
                ) * 0.5

                item_center = (
                    item["top"]
                    + item["bottom"]
                ) / 2

                line_center = (
                    line_top
                    + line_bottom
                ) / 2

                if abs(
                    item_center
                    - line_center
                ) <= tolerance:

                    line.append(item)
                    placed = True
                    break

            if not placed:
                lines.append([item])

        grouped_lines = []

        for line in lines:

            line.sort(
                key=lambda item: item["left"]
            )

            grouped_lines.append({
                "text": " ".join(
                    item["text"]
                    for item in line
                ),
                "left": min(
                    item["left"]
                    for item in line
                ),
                "top": min(
                    item["top"]
                    for item in line
                ),
                "right": max(
                    item["right"]
                    for item in line
                ),
                "bottom": max(
                    item["bottom"]
                    for item in line
                ),
                "confidence": min(
                    item["confidence"]
                    for item in line
                ),
            })

        grouped_lines.sort(
            key=lambda item: (
                item["top"],
                item["left"],
            )
        )

        return grouped_lines
from pathlib import Path

from app.ingestion.analyzer.page_renderer import PDFPageRenderer
from app.ingestion.extractor.vision_extractor import VisionExtractor


class VisualProcessor:

    def __init__(self):
        self.renderer = PDFPageRenderer()
        self.vision_extractor = VisionExtractor()

    def process_page(
        self,
        file_path: Path,
        page_number: int,
        output_dir: Path,
        source_file: str,
        document_id: str,
        start_order: int,
    ):

        image_path = self.renderer.render(
            file_path=file_path,
            page_number=page_number,
            output_dir=output_dir,
        )

        result = self.vision_extractor.extract(
            image_path
        )

        elements, next_order = (
            self.vision_extractor.to_elements(
                result=result,
                source_file=source_file,
                document_id=document_id,
                page_number=page_number,
                start_order=start_order,
            )
        )

        return elements, next_order
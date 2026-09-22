from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)


class DoclingConverter:

    def __init__(self):

        pdf_options = PdfPipelineOptions()

        pdf_options.do_ocr = False

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pdf_options
                )
            }
        )

    def convert(self, file_path: Path):

        result = self.converter.convert(
            file_path
        )

        return result.document
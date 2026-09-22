from pathlib import Path

from app.ingestion.base import DocumentParser
from app.ingestion.parsers.csv import CSVParser
from app.ingestion.parsers.docx import DOCXParser
from app.ingestion.parsers.image import ImageParser
from app.ingestion.parsers.pdf import PDFParser
from app.ingestion.parsers.pptx import PPTXParser
from app.ingestion.parsers.txt import TXTParser
from app.ingestion.parsers.xlsx import XLSXParser


class ParserRegistry:

    def __init__(self):
        self.parsers: dict[str, DocumentParser] = {
            ".pdf": PDFParser(),
            ".docx": DOCXParser(),
            ".pptx": PPTXParser(),
            ".xlsx": XLSXParser(),
            ".csv": CSVParser(),
            ".txt": TXTParser(),
            ".png": ImageParser(),
            ".jpg": ImageParser(),
            ".jpeg": ImageParser(),
        }

    def get_parser(self, file_path: Path) -> DocumentParser:
        extension = file_path.suffix.lower()

        parser = self.parsers.get(extension)

        if parser is None:
            raise ValueError(
                f"Unsupported file format: {extension}"
            )

        return parser
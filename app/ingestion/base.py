from abc import ABC, abstractmethod
from pathlib import Path

from app.ingestion.models import Document


class DocumentParser(ABC):

    @abstractmethod
    def parse(self, file_path: Path) -> Document:
        pass
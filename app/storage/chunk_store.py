import json
from pathlib import Path

from app.ingestion.models import (
    DocumentChunk,
    SourceLocation,
)

CHUNK_DIR = Path("data/chunks")


class LocalChunkStore:

    def __init__(
        self,
        storage_dir: Path = CHUNK_DIR,
    ):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        document_id: str,
        source_file: str,
        file_hash: str,
        chunks: list[DocumentChunk],
    ):

        file_path = (
            self.storage_dir
            / f"{document_id}.json"
        )

        data = {
            "document_id": document_id,
            "source_file": source_file,
            "file_hash": file_hash,
            "chunks": [
                self._serialize_chunk(chunk)
                for chunk in chunks
            ],
        }

        with file_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def load(
        self,
        document_id: str,
    ) -> list[DocumentChunk]:

        file_path = (
            self.storage_dir
            / f"{document_id}.json"
        )

        if not file_path.exists():
            return []

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return [
            self._deserialize_chunk(chunk)
            for chunk in data["chunks"]
        ]

    def exists(
        self,
        document_id: str,
    ) -> bool:

        return (
            self.storage_dir
            / f"{document_id}.json"
        ).exists()

    def load_all(self) -> list[DocumentChunk]:

        chunks = []

        for file_path in self.storage_dir.glob(
            "*.json"
        ):

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            chunks.extend(
                self._deserialize_chunk(chunk)
                for chunk in data["chunks"]
            )

        return chunks

    def find_by_hash(
        self,
        file_hash: str,
    ) -> tuple[str, list[DocumentChunk]] | None:

        for file_path in self.storage_dir.glob(
            "*.json"
        ):

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if data.get("file_hash") != file_hash:
                continue

            document_id = data["document_id"]

            chunks = [
                self._deserialize_chunk(chunk)
                for chunk in data["chunks"]
            ]

            return document_id, chunks

        return None

    def find_by_source_file(
        self,
        source_file: str,
    ) -> tuple[str, str, list[DocumentChunk]] | None:

        for file_path in self.storage_dir.glob(
            "*.json"
        ):

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if data.get("source_file") != source_file:
                continue

            document_id = data["document_id"]
            file_hash = data.get("file_hash")

            chunks = [
                self._deserialize_chunk(chunk)
                for chunk in data["chunks"]
            ]

            return (
                document_id,
                file_hash,
                chunks,
            )

        return None


    def delete(
        self,
        document_id: str,
    ) -> bool:

        file_path = (
            self.storage_dir
            / f"{document_id}.json"
        )

        if not file_path.exists():
            return False

        file_path.unlink()

        return True

    @staticmethod
    def _serialize_chunk(
        chunk: DocumentChunk,
    ) -> dict:

        return {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "text": chunk.text,
            "source_file": chunk.source_file,
            "locations": [
                location.__dict__
                for location in chunk.locations
            ],
            "element_types": chunk.element_types,
            "metadata": chunk.metadata,
        }

    @staticmethod
    def _deserialize_chunk(
        data: dict,
    ) -> DocumentChunk:

        locations = [
            SourceLocation(**location)
            for location in data["locations"]
        ]

        return DocumentChunk(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            text=data["text"],
            source_file=data["source_file"],
            locations=locations,
            element_types=data["element_types"],
            metadata=data["metadata"],
        )
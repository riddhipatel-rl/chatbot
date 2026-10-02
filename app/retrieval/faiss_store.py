import json
from pathlib import Path

import faiss
import numpy as np


class FAISSStore:
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.storage_dir / "index.faiss"
        self.ids_path = self.storage_dir / "chunk_ids.json"

        self.index = None
        self.chunk_ids = []

    def build(
        self,
        chunk_ids: list[str],
        embeddings,
    ):
        vectors = np.asarray(
            embeddings,
            dtype="float32",
        )

        if len(vectors) == 0:
            self.index = None
            self.chunk_ids = []
            return

        dimension = vectors.shape[1]

        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(vectors)

        self.chunk_ids = chunk_ids

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        self.ids_path.write_text(
            json.dumps(self.chunk_ids),
            encoding="utf-8",
        )

    def load(self):
        if not self.index_path.exists():
            return False

        if not self.ids_path.exists():
            return False

        self.index = faiss.read_index(
            str(self.index_path)
        )

        self.chunk_ids = json.loads(
            self.ids_path.read_text(
                encoding="utf-8"
            )
        )

        return True

    def search(
        self,
        embedding,
        top_k: int = 5,
    ):
        if self.index is None:
            return []

        vector = np.asarray(
            [embedding],
            dtype="float32",
        )

        scores, indices = self.index.search(
            vector,
            top_k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            results.append(
                {
                    "chunk_id": self.chunk_ids[index],
                    "score": float(score),
                }
            )

        return results
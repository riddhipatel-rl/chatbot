import re

from rank_bm25 import BM25Okapi

from app.ingestion.models import DocumentChunk


class BM25Retriever:

    def __init__(self, chunks: list[DocumentChunk]):
        self.chunks = chunks

        self.tokenized_chunks = [
            self._tokenize(chunk.text)
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(self.tokenized_chunks)

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> list[tuple[DocumentChunk, float]]:

        query_tokens = self._tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = scores.argsort()[::-1][:k]

        return [
            (
                self.chunks[index],
                float(scores[index]),
            )
            for index in ranked_indices
        ]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower(),
        )
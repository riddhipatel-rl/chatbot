from app.retrieval.bm25_search import BM25Retriever
from app.storage.chunk_store import LocalChunkStore


class RetrievalService:

    def __init__(self):
        self.chunk_store = LocalChunkStore()
        self.retriever = None
        self.refresh_index()

    def refresh_index(self):
        chunks = self.chunk_store.load_all()

        if not chunks:
            self.retriever = None
            return

        self.retriever = BM25Retriever(chunks)

    def search(self, query: str, k: int = 5):
        if self.retriever is None:
            return []

        return self.retriever.search(
            query=query,
            k=k,
        )

    def get_index_stats(self):
        if self.retriever is None:
            return {
                "chunks": 0,
                "files": [],
            }

        files = sorted(
            {
                chunk.source_file
                for chunk in self.retriever.chunks
            }
        )

        return {
            "chunks": len(self.retriever.chunks),
            "files": files,
        }


retrieval_service = RetrievalService()
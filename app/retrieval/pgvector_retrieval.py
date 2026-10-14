
from app.db.database import SessionLocal
from app.db.repositories.chunk_repository import ChunkRepository


class PgVectorRetriever:
    def search(
        self,
        embedding,
        top_k: int = 5,
    ) -> list[dict]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        query_embedding = embedding.tolist() if hasattr(
            embedding, "tolist"
        ) else list(embedding)

        with SessionLocal() as session:
            repository = ChunkRepository(session)

            matches = repository.similarity_search(
                query_embedding=query_embedding,
                top_k=top_k,
            )

        return [
            {
                "chunk_id": chunk.id,
                "score": 1.0 - distance,
            }
            for chunk, distance in matches
        ]

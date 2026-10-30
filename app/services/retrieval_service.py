import re

from app.retrieval.bm25_search import BM25Retriever
from app.retrieval.embedding_service import EmbeddingService
from app.db.database import SessionLocal
from app.db.repositories.chunk_repository import ChunkRepository
from app.retrieval.rrf import RRFFusion
from app.retrieval.reranker import Reranker
from app.services.visual_processing_service import VisualProcessingService
from app.retrieval.pgvector_retrieval import PgVectorRetriever
from app.core.tracing import trace_stage

class RetrievalService:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.pgvector_retriever = PgVectorRetriever()

        self.rrf = RRFFusion()
        self.reranker = Reranker()
        self.visual_processing_service = VisualProcessingService()
        

        self.chunks = []
        self.bm25 = None

        #self.refresh()

    def refresh(self):
        with SessionLocal() as session:
            repository = ChunkRepository(session)
            self.chunks = repository.get_latest_document_chunks()
            print(
                f"[STORAGE] Loaded {len(self.chunks)} chunks from PostgreSQL"
            )
            print(f"[STORAGE] BM25 initialized: {self.bm25 is not None}")

        if not self.chunks:
            self.bm25 = None
            print("[RETRIEVAL] No latest-version chunks found in PostgreSQL.")
            return

        self.bm25 = BM25Retriever(self.chunks)

        print(
            f"[RETRIEVAL] Loaded {len(self.chunks)} "
            "latest-version chunks from PostgreSQL."
        )
        print("[RETRIEVAL] BM25 index refreshed.")

    def refresh_index(self):
        self.refresh()

    def extract_page_number(
        self,
        query: str,
    ) -> int | None:

        match = re.search(
            r"\bpage\s+(\d+)\b",
            query.lower(),
        )

        if not match:
            return None

        return int(match.group(1))

    def search_specific_page(
        self,
        query: str,
        page_number: int,
        top_k: int,
    ):
        results = []

        for chunk in self.chunks:

            if not any(
                location.page == page_number
                for location in chunk.locations
            ):
                continue

            results.append(
                {
                    "chunk": chunk,
                    "rrf_score": 0.0,
                    "bm25_score": 0.0,
                    "dense_score": 0.0,
                }
            )

        results = results[:top_k]

        for result in results:
            chunk = result["chunk"]

            if "visual" not in chunk.element_types:
                result["visual_evidence"] = []
                continue

            result["visual_evidence"] = (
                self.visual_processing_service.process_chunk(
                    chunk,
                    query,
                )
            )

        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
    ):

        page_number = self.extract_page_number(query)

        if not self.chunks:
            return []

        if page_number is not None:
            print("Explicit page requested:", page_number)

            return self.search_specific_page(
                query=query,
                page_number=page_number,
                top_k=top_k,
            )

        candidate_k = max(top_k * 3, 20)

        chunk_map = {
            chunk.chunk_id: chunk
            for chunk in self.chunks
        }

        with trace_stage("bm25_search") as metrics:
            bm25_results = self.bm25.search(
                query,
                k=candidate_k,
            )
            metrics["candidate_count"] = len(bm25_results)


        target_bm25_rank = None

        for rank, (chunk, score) in enumerate(
            bm25_results,
            start=1,
        ):
            pages = sorted({
                location.page
                for location in chunk.locations
                if location.page
            })

            text_lower = chunk.text.lower()


        query_embedding = self.embedding_service.embed(
            [query]
        )[0]


        dense_results = self.pgvector_retriever.search(
            embedding=query_embedding,
            top_k=candidate_k,
        )


        target_dense_rank = None

        for rank, result in enumerate(
            dense_results,
            start=1,
        ):
            chunk = chunk_map.get(
                result["chunk_id"]
            )

            if chunk is None:
                continue

            pages = sorted({
                location.page
                for location in chunk.locations
                if location.page
            })
 
            print(
                f"Dense #{rank:02d} | "
                f"score={result['score']:.4f} | "
                f"pages={pages} | "
                f"chunk={chunk.chunk_id}"
            )

            text_lower = chunk.text.lower()

            if (
                "9%" in text_lower
                or "kdigo" in text_lower
                or "patient population" in text_lower
            ):
                print("   >>> TARGET-RELATED CHUNK")

                if target_dense_rank is None:
                    target_dense_rank = rank

        if target_dense_rank is None:
            print(
                "❌ Target-related page-2 chunk "
                "NOT FOUND in dense candidates"
            )
        else:
            print(
                f"✅ Target-related chunk found in Dense "
                f"at rank {target_dense_rank}"
            )

        bm25_ids = [
            chunk.chunk_id
            for chunk, _ in bm25_results
        ]

        dense_ids = [
            result["chunk_id"]
            for result in dense_results
        ]

        rrf_results = self.rrf.fuse(
            ranked_lists=[
                bm25_ids,
                dense_ids,
            ],
            top_k=candidate_k,
        )

        print("\n===================== RRF =====================")
        print("RRF candidates:", len(rrf_results)) 

        target_rrf_rank = None

        bm25_scores = {
            chunk.chunk_id: score
            for chunk, score in bm25_results
        }

        dense_scores = {
            result["chunk_id"]: result["score"]
            for result in dense_results
        }

        candidates = []

        for rank, (
            chunk_id,
            rrf_score,
        ) in enumerate(
            rrf_results,
            start=1,
        ):
            chunk = chunk_map.get(chunk_id)

            if chunk is None:
                continue

            pages = sorted({
                location.page
                for location in chunk.locations
                if location.page
            })

            print(
                f"RRF #{rank:02d} | "
                f"rrf={rrf_score:.6f} | "
                f"bm25={bm25_scores.get(chunk_id, 0.0):.4f} | "
                f"dense={dense_scores.get(chunk_id, 0.0):.4f} | "
                f"pages={pages} | "
                f"chunk={chunk_id}"
            )

            text_lower = chunk.text.lower()

            if (
                "9%" in text_lower
                or "kdigo" in text_lower
                or "patient population" in text_lower
            ):
                print("   >>> TARGET-RELATED CHUNK")

                if target_rrf_rank is None:
                    target_rrf_rank = rank

            candidates.append(
                {
                    "chunk": chunk,
                    "rrf_score": rrf_score,
                    "bm25_score": bm25_scores.get(
                        chunk_id,
                        0.0,
                    ),
                    "dense_score": dense_scores.get(
                        chunk_id,
                        0.0,
                    ),
                }
            )

        if target_rrf_rank is None:
            print(
                "❌ Target-related page-2 chunk "
                "NOT FOUND in RRF"
            )
        else:
            print(
                f"✅ Target-related chunk found in RRF "
                f"at rank {target_rrf_rank}"
            )


        results = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )

        print("\n================== RERANKER ==================")
        print("Reranked results:", len(results))

        target_reranker_rank = None

        for rank, result in enumerate(
            results,
            start=1,
        ):
            chunk = result["chunk"]

            pages = sorted({
                location.page
                for location in chunk.locations
                if location.page
            })

            print(
                f"Reranker #{rank:02d} | "
                f"pages={pages} | "
                f"chunk={chunk.chunk_id}"
            )

            text_lower = chunk.text.lower()

            if (
                "9%" in text_lower
                or "kdigo" in text_lower
                or "patient population" in text_lower
            ):
                print("   >>> TARGET-RELATED CHUNK")

                if target_reranker_rank is None:
                    target_reranker_rank = rank

        if target_reranker_rank is None:
            print(
                "❌ Target-related page-2 chunk "
                "NOT IN FINAL RESULTS"
            )
        else:
            print(
                f"✅ Target-related chunk is final result "
                f"#{target_reranker_rank}"
            )

        print("\n============================================================")
        print("                 RETRIEVAL DIAGNOSIS")
        print("============================================================")

        print(
            "BM25 rank:",
            target_bm25_rank,
        )

        print(
            "Dense rank:",
            target_dense_rank,
        )

        print(
            "RRF rank:",
            target_rrf_rank,
        )

        print(
            "Reranker rank:",
            target_reranker_rank,
        )

        print("============================================================\n")


        for result in results:
            result["visual_evidence"] = (
                self.visual_processing_service.process_chunk(
                    result["chunk"],
                    query,
                )
            )

        return results

    def build_context(self, results):

        context_parts = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            chunk = result["chunk"]

            context_parts.append(
                f"""
[Source {index}]
File: {chunk.source_file}
Pages: {
    [
        location.page
        for location in chunk.locations
        if location.page
    ]
}

Text:
{chunk.text}
"""
            )

            visual_evidence = result.get(
                "visual_evidence",
                [],
            )

            for visual in visual_evidence:
                visual_result = visual.get(
                    "visual_result",
                    {},
                )

                context_parts.append(
                    f"""
[Visual Evidence]
Page: {visual.get("page")}
Source: {visual_result.get("source")}
Answer: {visual_result.get("answer")}
Evidence: {visual_result.get("evidence")}
"""
                )

        return "\n".join(context_parts)
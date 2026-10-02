# app/api/retrieval.py

from fastapi import APIRouter
from httpcore import request
from pydantic import BaseModel

from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService

retrieval_service = RetrievalService()
llm_service = LLMService()

router = APIRouter(
    prefix="/query",
    tags=["Retrieval"],
)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 2


@router.post("")
async def query_documents(request: QueryRequest):

    print(">>> RETRIEVAL API CALLED")
    print(">>> QUERY:", request.query)

    results = retrieval_service.search(
        query=request.query,
        top_k=request.top_k,
    )
    print(">>> SEARCH RETURNED:", len(results))

    context = retrieval_service.build_context(results)
    
    print("\n========== FINAL LLM CONTEXT ==========")
    print(context)
    print("=======================================\n")

    answer = llm_service.generate(
        query=request.query,
        context=context,
    )

    return {
        "query": request.query,
        "answer": answer,
        "results": [
            {
                "rank": index,
                "chunk_id": result["chunk"].chunk_id,
                "document_id": result["chunk"].document_id,
                "source_file": result["chunk"].source_file,
                "text": result["chunk"].text,
                "metadata": result["chunk"].metadata,
                "visual_evidence": result.get(
                    "visual_evidence",
                    []
                ),
                "rrf_score": result.get("rrf_score"),
                "bm25_score": result.get("bm25_score"),
                "dense_score": result.get("dense_score"),
                "rerank_score": result.get("rerank_score"),
            }
            for index, result in enumerate(results, start=1)
        ],
    }
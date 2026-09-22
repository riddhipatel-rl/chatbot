from fastapi import APIRouter
from pydantic import BaseModel

from app.services.retrieval_service import retrieval_service


router = APIRouter(
    prefix="/query",
    tags=["Retrieval"],
)



class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("")
async def query_documents(
    request: QueryRequest,
):

    results = retrieval_service.search(
        query=request.query,
        k=request.top_k,
    )

    return {
        "query": request.query,
        "results": [
            {
                "rank": index,
                "score": score,
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "source_file": chunk.source_file,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "page": (
                    chunk.locations[0].page
                    if chunk.locations
                    else None
                ),
            }
            for index, (chunk, score)
            in enumerate(
                results,
                start=1,
            )
        ],
    }

@router.get("/debug")
async def retrieval_debug():

    return retrieval_service.get_index_stats()
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.ingestion import router as ingestion_router

from app.api.retrieval import (
    router as retrieval_router,
)

app = FastAPI(
    title="Document Chatbot API",
    version="1.0.0",
)


app.include_router(
    ingestion_router
)
app.include_router(
    retrieval_router
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    def fix_file_schema(obj):
        if isinstance(obj, dict):

            if obj.get("contentMediaType") == "application/octet-stream":
                obj.pop("contentMediaType", None)
                obj["format"] = "binary"

            for value in obj.values():
                fix_file_schema(value)

        elif isinstance(obj, list):

            for item in obj:
                fix_file_schema(item)

    fix_file_schema(schema)

    app.openapi_schema = schema

    return schema


app.openapi = custom_openapi


@app.get("/health")
async def health():

    return {
        "status": "ok"
    }
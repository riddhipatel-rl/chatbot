import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from pathlib import Path
from uuid import uuid4

import streamlit as st

from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import retrieval_service


st.set_page_config(
    page_title="Document RAG",
    page_icon="📄",
    layout="wide",
)


st.title("Document RAG")
st.caption("Multi-format document ingestion and BM25 retrieval")


if "search_results" not in st.session_state:
    st.session_state.search_results = None


ingestion_service = IngestionService()


st.header("Upload Documents")

uploaded_files = st.file_uploader(
    "Upload one or more documents",
    accept_multiple_files=True,
    type=[
        "pdf",
        "doc",
        "docx",
        "txt",
        "md",
        "xls",
        "xlsx",
        "csv",
        "ppt",
        "pptx",
        "jpg",
        "jpeg",
        "png",
        "html",
        "htm",
        "xml",
        "json",
        "zip",
    ],
)


if st.button(
    "Process Documents",
    type="primary",
):

    if not uploaded_files:
        st.warning(
            "Please select at least one file."
        )

    else:

        upload_dir = Path("uploads")
        upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        results = []

        try:

            with st.spinner(
                "Processing documents..."
            ):

                for file in uploaded_files:

                    extension = Path(
                        file.name
                    ).suffix.lower()

                    file_path = (
                        upload_dir
                        / f"{uuid4()}{extension}"
                    )

                    file_path.write_bytes(
                        file.getvalue()
                    )

                    if file.name.lower().endswith(
                        ".zip"
                    ):

                        zip_results = (
                            ingestion_service.ingest_zip(
                                file_path
                            )
                        )

                        for result in zip_results:
                            results.append({
                                "document_id": result[
                                    "document_id"
                                ],
                                "filename": result[
                                    "source_file"
                                ],
                                "chunks": result[
                                    "chunks"
                                ],
                                "cached": result[
                                    "cached"
                                ],
                            })

                    else:

                        result = (
                            ingestion_service.ingest(
                                file_path,
                                original_filename=file.name,
                            )
                        )

                        results.append({
                            "document_id": result[
                                "document_id"
                            ],
                            "filename": file.name,
                            "chunks": len(
                                result["chunks"]
                            ),
                            "cached": result[
                                "cached"
                            ],
                        })

                retrieval_service.refresh_index()

            st.success(
                f"Processed {len(results)} file(s)"
            )

            for result in results:

                status = (
                    "Reused"
                    if result["cached"]
                    else "Processed"
                )

                st.write(
                    f"**{result['filename']}** — "
                    f"{status}, "
                    f"{result['chunks']} chunks"
                )

        except Exception as error:

            st.error(
                f"Document processing failed: {error}"
            )


st.divider()


st.header("Search Documents")

with st.form("search_form"):

    query = st.text_input(
        "Enter your query",
        placeholder="e.g. What is QLoRA?",
    )

    search_submitted = st.form_submit_button(
        "Search",
        type="primary",
    )


if search_submitted:

    if not query.strip():

        st.warning(
            "Please enter a query."
        )

    else:

        try:

            results = retrieval_service.search(
                query=query,
                k=2,
            )

            formatted_results = []

            for index, (chunk, score) in enumerate(
                results,
                start=1,
            ):

                formatted_results.append({
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
                })

            st.session_state.search_results = (
                formatted_results
            )

        except Exception as error:

            st.session_state.search_results = None

            st.error(
                f"Search failed: {error}"
            )


if st.session_state.search_results is not None:

    if not st.session_state.search_results:

        st.info(
            "No relevant chunks found."
        )

    else:

        st.subheader("Top 2 Results")

        for result in st.session_state.search_results:

            with st.container(border=True):

                st.markdown(
                    f"### Result {result['rank']}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.caption(
                        f"Source: "
                        f"{result['source_file']}"
                    )

                    if result.get("page") is not None:

                        st.caption(
                            f"Page: "
                            f"{result['page']}"
                        )

                with col2:

                    st.caption(
                        f"BM25 Score: "
                        f"{result['score']:.3f}"
                    )

                st.markdown(
                    result["text"]
                )

                st.caption(
                    f"Chunk ID: "
                    f"{result['chunk_id']}"
                )
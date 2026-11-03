from pathlib import Path
from uuid import uuid4

import streamlit as st
import traceback

from app.core.upload_validation import (
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
    validate_upload,
)


SUPPORTED_TYPES = [
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
]


def render_upload_section(
    root_dir,
    sample_zip_path,
    ingestion_service,
    retrieval_service,
):
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title">📚 Documents</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Load sample documents or upload your own files."
        )

        st.markdown("### Sample Documents")

        if st.button(
            "✨ Load Sample Documents",
            type="primary",
            use_container_width=True,
            key="load_sample_documents",
        ):
            if not sample_zip_path.exists():
                st.error(
                    "Sample documents are not available."
                )

            else:
                try:
                    with st.spinner(
                        "Loading sample documents..."
                    ):
                        results = (
                            ingestion_service.ingest_zip(
                                sample_zip_path
                            )
                        )

                        retrieval_service.refresh_index()

                        for result in results:
                            st.session_state.loaded_documents.add(
                                result["source_file"]
                            )

                        st.session_state.sample_loaded = True

                    st.success(
                        f"Loaded {len(results)} sample document(s)."
                    )

                except Exception as error:
                    st.error(
                        f"Unable to load sample documents: {error}"
                    )

        st.markdown("### Upload Documents")

        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=SUPPORTED_TYPES,
            help=f"Maximum {MAX_UPLOAD_SIZE_MB} MB per file",
            key="document_uploader",
        )

        if uploaded_files:
            if st.button(
                "Process Uploaded Documents",
                use_container_width=True,
                key="process_uploaded_documents",
            ):
                upload_dir = root_dir / "uploads"

                upload_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                results = []

                try:
                    with st.spinner(
                        "Processing your documents..."
                    ):
                        for file in uploaded_files:
                            
                            extension = Path(file.name).suffix.lower()

                            if file.size > MAX_UPLOAD_SIZE_BYTES:
                                st.error(
                                    f"{file.name}: File exceeds "
                                    f"{MAX_UPLOAD_SIZE_MB} MB."
                                )
                                continue

                            try:
                                validate_upload(
                                    filename=file.name,
                                    size_bytes=file.size,
                                    header=file.getvalue()[:16],
                                    allow_zip=True,
                                )
                            except ValueError as error:
                                st.error(f"{file.name}: {error}")
                                continue

                            file_path = (
                                upload_dir / f"{uuid4()}{extension}"
                            )

                            try:
                                file_path.write_bytes(file.getvalue())

                                if extension == ".zip":
                                    zip_results = (
                                        ingestion_service.ingest_zip(
                                            file_path
                                        )
                                    )

                                    for result in zip_results:
                                        results.append({
                                            "filename": result["source_file"],
                                            "cached": result["cached"],
                                        })
                                else:
                                    result = ingestion_service.ingest(
                                        file_path,
                                        original_filename=file.name,
                                    )

                                    results.append({
                                        "filename": file.name,
                                        "cached": result["cached"],
                                    })
                            finally:
                                file_path.unlink(missing_ok=True)


                        retrieval_service.refresh_index()

                        for result in results:
                            st.session_state.loaded_documents.add(
                                result["filename"]
                            )

                    st.success(
                        f"Loaded {len(results)} document(s)."
                    )

                except Exception as error:
                    traceback.print_exc()
                    st.error(
                        f"Document processing failed: {error}"
                    )

        if st.session_state.loaded_documents:
            st.markdown("### Loaded Documents")

            for document in sorted(
                st.session_state.loaded_documents
            ):
                st.markdown(
                    f"📄 {document}"
                )
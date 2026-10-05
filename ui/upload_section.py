from pathlib import Path
from uuid import uuid4

import streamlit as st


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
            help="Maximum 200 MB per file",
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
                                    results.append(
                                        {
                                            "filename": result[
                                                "source_file"
                                            ],
                                            "cached": result[
                                                "cached"
                                            ],
                                        }
                                    )

                            else:
                                result = (
                                    ingestion_service.ingest(
                                        file_path,
                                        original_filename=file.name,
                                    )
                                )

                                results.append(
                                    {
                                        "filename": file.name,
                                        "cached": result[
                                            "cached"
                                        ],
                                    }
                                )

                        retrieval_service.refresh_index()

                        for result in results:
                            st.session_state.loaded_documents.add(
                                result["filename"]
                            )

                    st.success(
                        f"Loaded {len(results)} document(s)."
                    )

                except Exception as error:
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
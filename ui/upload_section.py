from pathlib import Path
from uuid import uuid4
from pathlib import Path

import streamlit as st


def render_upload_section(root_dir, sample_zip_path, ingestion_service, retrieval_service):
    st.markdown(
        '<div class="section-title">Try the demo</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "Explore the system with preloaded sample documents, "
        "or upload your own files."
    )


    sample_col, upload_col = st.columns([1, 1], gap="medium")


    with sample_col:

        st.markdown(
            """
            <div class="demo-card">
                <div class="demo-card-title">✨ Explore with sample documents</div>
                <div class="demo-card-text">
                    Load the built-in multi-format demo files and try the suggested questions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Try Sample Documents",
            type="primary",
            use_container_width=True,
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


    with upload_col:

        uploaded_files = st.file_uploader(
            "Upload documents",
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
            label_visibility="collapsed",
            help="Maximum 200 MB per file",
        )

        st.markdown(
            '<div class="upload-help">PDF, DOCX, TXT, MD, XLSX, CSV, PPTX, JPG, PNG, HTML, XML, JSON and ZIP · up to 200 MB per file</div>',
            unsafe_allow_html=True,
        )


    if uploaded_files:

        if st.button(
            "Process Uploaded Documents",
            use_container_width=True,
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

        st.markdown(
            '<div class="section-title">Documents in this session</div>',
            unsafe_allow_html=True,
        )

        for document in sorted(
            st.session_state.loaded_documents
        ):

            st.markdown(
                f"📄 `{document}`"
            )


    st.divider()



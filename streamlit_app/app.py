import requests
import streamlit as st


API_URL = "http://localhost:8000"


st.set_page_config(
    page_title="Document RAG",
    page_icon="📄",
    layout="wide",
)


st.title("Document RAG")
st.caption("Multi-format document ingestion and BM25 retrieval")


if "search_results" not in st.session_state:
    st.session_state.search_results = None


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

        files = [
            (
                "files",
                (
                    file.name,
                    file.getvalue(),
                    file.type,
                ),
            )
            for file in uploaded_files
        ]

        try:

            response = requests.post(
                f"{API_URL}/documents/upload-multiple",
                files=files,
                timeout=300,
            )

            response.raise_for_status()

            data = response.json()

            st.success(
                f"Processed "
                f"{data['total_files']} file(s)"
            )


        except requests.RequestException as error:

            st.error(
                f"Upload failed: {error}"
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
        st.warning("Please enter a query.")
    else:
        try:
            response = requests.post(
                f"{API_URL}/query",
                json={
                    "query": query,
                    "top_k": 2,
                },
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()

            st.session_state.search_results = data["results"]

        except requests.RequestException as error:
            st.session_state.search_results = None
            st.error(f"Search failed: {error}")

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
                        f"Source: {result['source_file']}"
                    )

                    if result.get("page") is not None:
                        st.caption(
                            f"Page: {result['page']}"
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
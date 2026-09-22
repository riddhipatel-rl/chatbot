import streamlit as st


def render_question_section(retrieval_service):
    SAMPLE_QUERIES = [
        {
            "question": "What is Effective Threat Modelling?",
            "document": "Effective_Threat_Modeling_using_TAM.docx",
        },
        {
            "question": "How to overcome Nervousness?",
            "document": "Presentation.pptx",
        },
        {
            "question": "What is Middleware?",
            "document": "Introduction to HTTP.txt",
        },
        {
            "question": "What is DLBCL?",
            "document": "scanned.pdf",
        },
        {
            "question": "What happened during the terrible storm?",
            "document": "the_lantern_keeper_of_bellwood.md",
        },
    ]
    if (
        st.session_state.sample_loaded
        and SAMPLE_QUERIES
    ):

        st.markdown(
            '<div class="section-title">Suggested questions</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Click a question to try it."
        )

        for index, item in enumerate(
            SAMPLE_QUERIES
        ):

            question = item["question"]
            document = item["document"]

            question_col, source_col = st.columns(
                [5.8, 2.2],
                gap="small",
            )

            with question_col:

                if st.button(
                    question,
                    key=f"sample_query_{index}",
                    use_container_width=True,
                ):

                    st.session_state.query = question
                    st.session_state.search_results = None

            with source_col:

                st.markdown(
                    f'<div class="question-source"><span class="question-source-icon">📄</span>{document}</div>',
                    unsafe_allow_html=True,
                )



    st.markdown(
        """
        <div class="ask-header">
            <div class="ask-icon">💬</div>
            <div>
                <div class="ask-title">Ask your own question</div>
                <div class="ask-subtitle">
                    Ask anything about your loaded documents.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    with st.form("search_form"):

        query_col, button_col = st.columns(
            [6.5, 1],
            gap="medium",
            vertical_alignment="center",
        )

        with query_col:

            query = st.text_input(
                "Question",
                value=st.session_state.query,
                placeholder="Ask anything about your documents...",
                label_visibility="collapsed",
            )

        with button_col:

            search_submitted = st.form_submit_button(
                "➤  Ask",
                type="primary",
                use_container_width=True,
            )


    if search_submitted:

        st.session_state.query = query

        if not query.strip():

            st.warning(
                "Please enter a question."
            )

        elif not st.session_state.loaded_documents:

            st.info(
                "Load sample documents or upload your own documents first."
            )

        else:

            try:

                with st.spinner(
                    "Finding relevant information..."
                ):

                    results = retrieval_service.search(
                        query=query,
                        k=2,
                    )

                formatted_results = []

                for rank, (chunk, score) in enumerate(
                    results,
                    start=1,
                ):

                    formatted_results.append(
                        {
                            "rank": rank,
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
                    )

                st.session_state.search_results = (
                    formatted_results
                )

            except Exception as error:

                st.session_state.search_results = None

                st.error(
                    f"Search failed: {error}"
                )



import streamlit as st


TEXT_SAMPLE_QUERIES = [
    {
        "question": "What is Effective Threat Modelling?",
        "document": "ETM.docx",
    },
    {
        "question": "What is Middleware?",
        "document": "Introduction to HTTP.txt",
    },
    {
        "question": "What happened during the terrible storm?",
        "document": "the_lantern_story.md",
    },
    {
        "question": "What types of blood diseases does Roche develop medicines for?",
        "document": "scanned.pdf",
    },
]


VISION_SAMPLE_QUERIES = [
    {
        "question": "Look at Figure 15. What type of visualization is used to display malaria service readiness results?",
        "document": "hhfa.pdf",
    },
    {
        "question": "What does the A2 albuminuria category represent?",
        "document": "visual.pdf",
    },
    {
        "question": "How many facilities were included in the national analysis shown in the table?",
        "document": "hhfa.pdf",
    },
]


def _run_question(
    question: str,
    answer_service,
):
    st.session_state.query = question

    with st.spinner(
        "Finding relevant information..."
    ):
        answer = answer_service.answer(
            query=question,
            top_k=2,
        )

    st.session_state.answer = answer
    st.session_state.search_results = None


def _render_sample_questions(
    title,
    questions,
    answer_service,
    key_prefix,
):
    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )

    for index, item in enumerate(
        questions
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
                key=f"{key_prefix}_{index}",
                use_container_width=True,
            ):
                try:
                    _run_question(
                        question,
                        answer_service,
                    )

                except Exception as error:
                    st.session_state.answer = None

                    st.error(
                        f"Search failed: {error}"
                    )

        with source_col:

            icon = (
                "📄"
                if key_prefix == "text"
                else "📊"
            )

            st.markdown(
                f"""
                <div class="question-source">
                    <span class="question-source-icon">
                        {icon}
                    </span>
                    {document}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_question_section(
    answer_service,
):
    if st.session_state.sample_loaded:

        st.markdown(
            '<div class="section-title">Suggested questions</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "Choose a question to test the document RAG pipeline."
        )

        _render_sample_questions(
            "Text-based questions",
            TEXT_SAMPLE_QUERIES,
            answer_service,
            "text",
        )

        _render_sample_questions(
            "Vision-based questions",
            VISION_SAMPLE_QUERIES,
            answer_service,
            "vision",
        )

    st.markdown(
        """
        <div class="ask-header">
            <div class="ask-icon">💬</div>
            <div>
                <div class="ask-title">
                    Ask your own question
                </div>
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
                placeholder=(
                    "Ask anything about your documents..."
                ),
                label_visibility="collapsed",
            )

        with button_col:

            search_submitted = (
                st.form_submit_button(
                    "➤  Ask",
                    type="primary",
                    use_container_width=True,
                )
            )

    if search_submitted:

        st.session_state.query = query

        if not query.strip():

            st.warning(
                "Please enter a question."
            )

        elif not st.session_state.loaded_documents:

            st.info(
                "Load sample documents or upload "
                "your own documents first."
            )

        else:

            try:

                _run_question(
                    query,
                    answer_service,
                )

            except Exception as error:

                st.session_state.answer = None

                st.error(
                    f"Search failed: {error}"
                )
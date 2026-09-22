import streamlit as st


def render_header():
    st.markdown(
        '<div class="main-title">📄 Document RAG</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Ask questions across your documents using intelligent document retrieval."
        "</div>",
        unsafe_allow_html=True,
    )



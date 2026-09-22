import streamlit as st


def render_results():
    if st.session_state.search_results is not None:

        st.divider()

        if not st.session_state.search_results:

            st.info(
                "No relevant information was found in the loaded documents."
            )

        else:

            st.markdown(
                """
                <div class="relevant-header">
                    <div class="relevant-icon">📄</div>
                    <div>
                        <div class="relevant-title">Relevant information</div>
                        <div class="relevant-subtitle">
                            Information retrieved from your documents.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for result in st.session_state.search_results:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        result["text"]
                    )

                    source_text = (
                        f"📄 {result['source_file']}"
                    )

                    if result.get("page") is not None:

                        source_text += (
                            f"  ·  Page {result['page']}"
                        )

                    st.caption(
                        source_text
                    )

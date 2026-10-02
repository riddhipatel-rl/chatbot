import streamlit as st


def render_results():

    answer = st.session_state.get("answer")

    if answer is None:
        return

    st.divider()

    st.markdown(
        """
        <div class="relevant-header">
            <div class="relevant-icon">💡</div>
            <div>
                <div class="relevant-title">Answer</div>
                <div class="relevant-subtitle">
                    Answer generated from the retrieved document evidence.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer_text = answer.get("answer")

    if answer_text:
        st.markdown(answer_text)
    else:
        st.info("No answer was generated.")

    sources = answer.get("sources", [])

    if not sources:
        return

    st.markdown("### Sources")

    for source in sources:

        file_name = source.get(
            "file",
            "Unknown document",
        )

        pages = source.get(
            "pages",
            [],
        )

        with st.container(border=True):

            st.markdown(
                f"📄 **{file_name}**"
            )

            if pages:
                page_text = ", ".join(
                    str(page)
                    for page in pages
                )

                st.caption(
                    f"Page(s): {page_text}"
                )

            evidence = source.get(
                "evidence",
                [],
            )

            if not evidence:
                continue

            st.markdown("**Evidence**")

            for item in evidence:

                evidence_type = item.get(
                    "type"
                )

                title = item.get(
                    "title"
                )

                evidence_text = item.get(
                    "evidence"
                )

                page = item.get(
                    "page"
                )

                if evidence_type == "vision":

                    st.markdown(
                        "📊 **Vision evidence**"
                    )

                elif evidence_type == "visual_text":

                    st.markdown(
                        "📊 **Extracted visual content**"
                    )

                else:

                    continue

                if title:

                    st.markdown(
                        f"**{title}**"
                    )

                if page is not None:

                    st.caption(
                        f"Page {page}"
                    )

                if evidence_text:

                    st.write(
                        evidence_text
                    )
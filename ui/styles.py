import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #6b7280;
            font-size: 1.05rem;
            margin-bottom: 2rem;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.35rem;
        }

        .demo-card {
            background: #171a21;
            border: 1px solid #2d313b;
            border-radius: 0.9rem;
            padding: 1rem 1.1rem 0.9rem;
            min-height: 112px;
        }

        .demo-card-title {
            font-size: 0.92rem;
            font-weight: 600;
            margin-bottom: 0.2rem;
        }

        .demo-card-text {
            color: #8b93a5;
            font-size: 0.78rem;
            line-height: 1.35;
            margin-bottom: 0.7rem;
        }

        .upload-help {
            color: #8b93a5;
            font-size: 0.76rem;
            margin-top: -0.35rem;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: #171a21;
            border: 1px dashed #4b5261;
            border-radius: 0.9rem;
            padding: 0.65rem 0.8rem;
            min-height: 112px;
            transition: border-color 0.2s ease, background 0.2s ease;
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: #7c8598;
            background: #1b1f27;
        }

        [data-testid="stFileUploaderDropzone"] button {
            border-radius: 0.55rem !important;
        }

        .question-source {
            display: inline-flex;
            align-items: center;
            max-width: 100%;
            padding: 0.38rem 0.65rem;
            border-radius: 999px;
            background: #171a21;
            border: 1px solid #303541;
            color: #9aa2b1;
            font-size: 0.72rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .question-source-icon {
            margin-right: 0.35rem;
        }

        div[data-testid="stHorizontalBlock"] {
            align-items: center;
        }

        .sample-question-row {
            margin-bottom: 0.45rem;
        }

        .document-name {
            color: #6b7280;
            font-size: 0.85rem;
        }

        .ask-header {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }

        .ask-icon {
            width: 42px;
            height: 42px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: #172554;
            border: 1px solid #29458f;
            font-size: 1.25rem;
        }

        .ask-title {
            font-size: 1.35rem;
            font-weight: 650;
            line-height: 1.2;
        }

        .ask-subtitle {
            color: #8b93a5;
            font-size: 0.88rem;
            margin-top: 0.2rem;
        }

        div[data-testid="stForm"] {
            background: linear-gradient(135deg, #11161f 0%, #151b26 100%);
            border: 1px solid #283142;
            border-radius: 1rem;
            padding: 1.25rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.16);
        }

        div[data-testid="stForm"] [data-testid="stTextInput"] input {
            height: 3.15rem;
            background: #171d28;
            border: 1px solid #3b4658;
            border-radius: 0.7rem;
            color: #f3f4f6;
            padding: 0 1rem;
            font-size: 0.92rem;
        }

        div[data-testid="stForm"] [data-testid="stTextInput"] input:focus {
            border-color: #4f7cff;
            box-shadow: 0 0 0 1px #4f7cff;
        }

        div[data-testid="stForm"] [data-testid="stTextInput"] input::placeholder {
            color: #687386;
        }

        div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
            height: 3.15rem;
            border-radius: 0.7rem;
            background: linear-gradient(135deg, #4f6df5, #6366f1);
            border: 1px solid #6478f6;
            font-weight: 600;
            transition: transform 0.15s ease, filter 0.15s ease;
        }

        div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
            filter: brightness(1.08);
            transform: translateY(-1px);
        }

        .relevant-header {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin-top: 0.5rem;
        }

        .relevant-icon {
            width: 42px;
            height: 42px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: #063b3b;
            border: 1px solid #0f766e;
            font-size: 1.2rem;
        }

        .relevant-title {
            font-size: 1.35rem;
            font-weight: 650;
        }

        .relevant-subtitle {
            color: #8b93a5;
            font-size: 0.88rem;
            margin-top: 0.2rem;
        }
        button[kind="primary"] {
            background: linear-gradient(135deg, #4f6df5, #6366f1) !important;
            border: 1px solid #6478f6 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

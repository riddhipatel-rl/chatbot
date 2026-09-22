import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

SAMPLE_ZIP_PATH = (
    ROOT_DIR
    / "sample_documents"
    / "multiple_files.zip"
)

from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import retrieval_service
from ui.header import render_header
from ui.question_section import render_question_section
from ui.results_section import render_results
from ui.styles import apply_styles
from ui.upload_section import render_upload_section


if "search_results" not in st.session_state:
    st.session_state.search_results = None

if "query" not in st.session_state:
    st.session_state.query = ""

if "loaded_documents" not in st.session_state:
    st.session_state.loaded_documents = set()

if "sample_loaded" not in st.session_state:
    st.session_state.sample_loaded = False


st.set_page_config(
    page_title="Document RAG",
    page_icon="📄",
    layout="wide",
)


ingestion_service = IngestionService()

apply_styles()
render_header()

render_upload_section(
    ROOT_DIR,
    SAMPLE_ZIP_PATH,
    ingestion_service,
    retrieval_service,
)

render_question_section(retrieval_service)

render_results()

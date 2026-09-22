from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".md",
    ".xls",
    ".xlsx",
    ".csv",
    ".ppt",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
    ".html",
    ".htm",
    ".xml",
    ".json",
}


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_supported(filename: str) -> bool:
    return get_extension(filename) in SUPPORTED_EXTENSIONS
from pathlib import Path

from app.ingestion.registry import ParserRegistry


def main():
    file_path = Path("uploads/Introduction to HTTP.txt")

    registry = ParserRegistry()

    parser = registry.get_parser(file_path)

    document = parser.parse(file_path)

    print(f"Document ID: {document.document_id}")
    print(f"File: {document.file_name}")
    print(f"Type: {document.file_type}")
    print(f"Elements: {len(document.elements)}")

    for element in document.elements[:5]:
        print("\n----------------")
        print(f"Type: {element.element_type}")
        print(f"Location: {element.location}")
        print(f"Text: {element.text[:300]}")


if __name__ == "__main__":
    main()
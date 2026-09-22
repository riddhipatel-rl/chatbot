from pathlib import Path
from uuid import uuid4

import pandas as pd

from app.ingestion.base import DocumentParser
from app.ingestion.models import Document, DocumentElement


class CSVParser(DocumentParser):

    def parse(self, file_path: Path) -> Document:
        document_id = str(uuid4())

        dataframe = pd.read_csv(file_path)

        elements = []

        for index, row in dataframe.iterrows():

            values = [
                f"{column}: {row[column]}"
                for column in dataframe.columns
                if pd.notna(row[column])
            ]

            if not values:
                continue

            text = " | ".join(values)

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    element_type="row",
                    text=text,
                    metadata={
                        "row": int(index) + 2,
                    },
                )
            )

        return Document(
            document_id=document_id,
            file_name=file_path.name,
            file_type="csv",
            elements=elements,
        )
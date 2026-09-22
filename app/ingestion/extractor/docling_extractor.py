from pathlib import Path
from uuid import uuid4

from docling_core.types.doc import DoclingDocument
from streamlit import table

from app.ingestion.models import (
    CanonicalDocument,
    DocumentElement,
    SourceLocation,
)
from app.ingestion.text_normalizer import TextNormalizer

class DoclingExtractor:

    def __init__(self):
        self.normalizer = TextNormalizer()

    def extract(
        self,
        document: DoclingDocument,
        source_file: str,
    ) -> CanonicalDocument:

        document_id = str(uuid4())

        elements = []

        for order, (item, level) in enumerate(
            document.iterate_items()
        ):
            label = str(
                getattr(item, "label", "")
            )

            if label == "table":
                table_elements = self._extract_table(
                    item,
                    source_file,
                    order,
                )

                elements.extend(table_elements)
                continue

            text = getattr(item, "text", "")

            if not text:
                continue

            text = self.normalizer.normalize(text)

            if not text:
                continue

            provenance = getattr(item, "prov", [])

            if provenance:
                for prov in provenance:
                    location = SourceLocation(
                        page=prov.page_no,
                        bbox={
                            "left": prov.bbox.l,
                            "bottom": prov.bbox.b,
                            "right": prov.bbox.r,
                            "top": prov.bbox.t,
                        },
                    )

                    elements.append(
                        self._create_element(
                            text=text,
                            label=label,
                            source_file=source_file,
                            order=order,
                            location=location,
                            parent=item,
                            level=level,
                        )
                    )
            else:
                elements.append(
                    self._create_element(
                        text=text,
                        label=label,
                        source_file=source_file,
                        order=order,
                        parent=item,
                        level=level,
                    )
                )

        return CanonicalDocument(
            document_id=document_id,
            source_file=source_file,
            file_type=Path(source_file).suffix.lower(),
            elements=elements,
        )

    def _create_element(
        self,
        text: str,
        label: str,
        source_file: str,
        order: int,
        location: SourceLocation | None = None,
        parent=None,
        level=None,
        document_id: str | None = None,
    ) -> DocumentElement:

        parent_id = None

        if parent is not None:
            parent_id = str(
                getattr(parent, "self_ref", "")
            ) or None

        return DocumentElement(
            element_id=str(uuid4()),
            text=text,
            element_type=label,
            source_file=source_file,
            order=order,
            location=location or SourceLocation(),
            parent_id=parent_id,
            metadata={
                "level": level,
                "docling_ref": parent_id,
            },
        )

    def _extract_table(
        self,
        table,
        source_file: str,
        order: int,
    ) -> list[DocumentElement]:

        elements = []

        grid = table.data.grid

        if not grid:
            return elements

        rows = []

        for row in grid:
            row_cells = []

            for cell in row:
                text = getattr(
                    cell,
                    "text",
                    "",
                )

                text = self.normalizer.normalize(
                    text
                )

                row_cells.append(text)

            if any(row_cells):
                rows.append(row_cells)

        if not rows:
            return elements

        headers = rows[0]

        table_caption = getattr(
            table,
            "caption",
            None,
        )

        if table_caption:
            table_caption = self.normalizer.normalize(
                str(table_caption)
            )

        table_provenance = getattr(
            table,
            "prov",
            [],
        )

        table_location = SourceLocation()

        if table_provenance:
            prov = table_provenance[0]

            table_location = SourceLocation(
                page=prov.page_no,
                bbox={
                    "left": prov.bbox.l,
                    "bottom": prov.bbox.b,
                    "right": prov.bbox.r,
                    "top": prov.bbox.t,
                },
            )

        for row_index, row in enumerate(rows):

            row_start = None
            row_end = None
            column_start = None
            column_end = None

            for cell in grid[row_index]:

                cell_row_start = getattr(
                    cell,
                    "start_row_offset_idx",
                    None,
                )

                cell_row_end = getattr(
                    cell,
                    "end_row_offset_idx",
                    None,
                )

                cell_column_start = getattr(
                    cell,
                    "start_col_offset_idx",
                    None,
                )

                cell_column_end = getattr(
                    cell,
                    "end_col_offset_idx",
                    None,
                )

                if row_start is None:
                    row_start = cell_row_start

                if row_end is None:
                    row_end = cell_row_end

                if column_start is None:
                    column_start = cell_column_start

                if (
                    cell_column_end is not None
                    and (
                        column_end is None
                        or cell_column_end > column_end
                    )
                ):
                    column_end = cell_column_end

            row_values = []

            for index, value in enumerate(row):

                if index < len(headers):
                    header = headers[index]

                    if header:
                        row_values.append(
                            f"{header}: {value}"
                        )
                    else:
                        row_values.append(value)
                else:
                    row_values.append(value)

            row_text = " | ".join(
                value
                for value in row_values
                if value
            )

            if not row_text:
                continue

            context_parts = []

            if table_caption:
                context_parts.append(
                    f"Table: {table_caption}"
                )

            context_parts.append(
                "Columns: "
                + " | ".join(
                    header
                    for header in headers
                    if header
                )
            )

            context_parts.append(
                f"Row: {row_text}"
            )

            text = "\n".join(
                context_parts
            )

            elements.append(
                DocumentElement(
                    element_id=str(uuid4()),
                    text=text,
                    element_type="table_row",
                    source_file=source_file,
                    order=order + row_index,
                    location=SourceLocation(
                        page=table_location.page,
                        bbox=table_location.bbox,
                        row_start=row_start,
                        row_end=row_end,
                        column_start=column_start,
                        column_end=column_end,
                    ),
                    metadata={
                        "source": "table",
                        "table_caption": table_caption,
                        "column_headers": headers,
                        "row_index": row_index,
                    },
                )
            )

        return elements
from pathlib import Path

import pymupdf


class PDFPageRenderer:

    def render(
        self,
        file_path: Path,
        page_number: int,
        output_dir: Path,
    ) -> Path:

        output_dir.mkdir(parents=True, exist_ok=True)

        document = pymupdf.open(file_path)

        try:
            page = document[page_number - 1]

            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                alpha=False,
            )

            output_path = output_dir / f"page_{page_number}.png"

            pixmap.save(output_path)

            return output_path

        finally:
            document.close()

    def render_region(
        self,
        file_path: Path,
        page_number: int,
        bbox: dict[str, float],
        output_dir: Path,
    ) -> Path:

        output_dir.mkdir(parents=True, exist_ok=True)

        document = pymupdf.open(file_path)

        try:
            page = document[page_number - 1]

            rect = pymupdf.Rect(
                bbox["x0"],
                bbox["y0"],
                bbox["x1"],
                bbox["y1"],
            )

            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                clip=rect,
                alpha=False,
            )

            output_path = (
                output_dir
                / f"page_{page_number}_region.png"
            )

            pixmap.save(output_path)

            return output_path

        finally:
            document.close()
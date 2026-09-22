from pathlib import Path
import subprocess


class PDFOCRProcessor:

    def make_searchable(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Path:

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        subprocess.run(
            [
                "ocrmypdf",
                "--force-ocr",
                "--skip-big",
                "100",
                "--output-type",
                "pdf",
                str(input_path),
                str(output_path),
            ],
            check=True,
        )

        return output_path
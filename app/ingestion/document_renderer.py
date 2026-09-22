from pathlib import Path
import subprocess


class DocumentRenderer:

    def render_to_pdf(
        self,
        input_path: Path,
        output_dir: Path,
    ) -> Path:

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(input_path),
            ],
            check=True,
        )

        output_path = (
            output_dir
            / f"{input_path.stem}.pdf"
        )

        if not output_path.exists():
            raise FileNotFoundError(
                f"LibreOffice did not create: {output_path}"
            )

        return output_path
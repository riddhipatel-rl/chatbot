from pathlib import Path
from zipfile import ZipFile


class ZipExtractor:

    def extract(
        self,
        zip_path: Path,
        output_dir: Path,
    ) -> list[Path]:

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        extracted_files = []

        with ZipFile(zip_path, "r") as archive:

            for member in archive.infolist():

                if member.is_dir():
                    continue

                target_path = (
                    output_dir / member.filename
                ).resolve()

                if not str(target_path).startswith(
                    str(output_dir.resolve())
                ):
                    raise ValueError(
                        "Unsafe ZIP file path detected"
                    )

                target_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with archive.open(member) as source:
                    with target_path.open("wb") as target:
                        target.write(source.read())

                extracted_files.append(
                    target_path
                )

        return extracted_files
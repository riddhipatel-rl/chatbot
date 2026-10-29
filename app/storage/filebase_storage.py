import hashlib
import mimetypes
import os
import tempfile
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.config import Config
from dotenv import load_dotenv


load_dotenv()


def get_setting(name: str) -> str | None:
    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st

        value = st.secrets.get(name)

        if value:
            return str(value)
    except Exception:
        pass

    return None


class FilebaseStorage:
    def __init__(self):
        self.bucket = get_setting("FILEBASE_BUCKET")
        self.access_key = get_setting("FILEBASE_KEY")
        self.secret_key = get_setting("FILEBASE_SECRET")
        self.endpoint = "https://s3.filebase.io"
        self.client = None

    def _get_client(self):
        if not all(
            [self.bucket, self.access_key, self.secret_key]
        ):
            raise RuntimeError(
                "Filebase is not configured. Check FILEBASE_KEY, "
                "FILEBASE_SECRET and FILEBASE_BUCKET."
            )

        if self.client is None:
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                region_name="auto",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(
                    signature_version="s3v4",
                ),
            )

        return self.client

    def upload_file(
        self,
        file_path: Path,
        object_key: str,
    ) -> str:
        file_path = Path(file_path)

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Cannot upload missing file: {file_path}"
            )

        content_type, _ = mimetypes.guess_type(file_path.name)

        self._get_client().upload_file(
            str(file_path),
            self.bucket,
            object_key,
            ExtraArgs={
                "ContentType": (
                    content_type or "application/octet-stream"
                ),
                "ServerSideEncryption": "AES256",
            },
        )

        print(f"[FILEBASE] Uploaded: {object_key}")
        return object_key

    def download_to_cache(self, object_key: str) -> Path:
        cache_dir = (
            Path(tempfile.gettempdir())
            / "document-rag-filebase-cache"
        )
        cache_dir.mkdir(parents=True, exist_ok=True)

        key_hash = hashlib.sha256(
            object_key.encode("utf-8")
        ).hexdigest()

        suffix = Path(object_key).suffix.lower()
        local_path = cache_dir / f"{key_hash}{suffix}"

        if local_path.is_file() and local_path.stat().st_size > 0:
            return local_path

        temporary_path = cache_dir / (
            f".{key_hash}.{uuid4().hex}.part"
        )

        try:
            self._get_client().download_file(
                self.bucket,
                object_key,
                str(temporary_path),
            )

            if not temporary_path.is_file():
                raise FileNotFoundError(
                    f"Filebase download failed: {object_key}"
                )

            os.replace(temporary_path, local_path)

        finally:
            temporary_path.unlink(missing_ok=True)

        print(f"[FILEBASE] Downloaded: {object_key}")
        return local_path

    def delete_file(self, object_key: str) -> None:
        self._get_client().delete_object(
            Bucket=self.bucket,
            Key=object_key,
        )

        print(f"[FILEBASE] Deleted test object: {object_key}")
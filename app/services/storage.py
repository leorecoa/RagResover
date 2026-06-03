import io
import re
from pathlib import PurePath
from uuid import uuid4

import urllib3
from anyio import to_thread
from minio import Minio

from app.core.config import settings


SAFE_OBJECT_RE = re.compile(r"[^A-Za-z0-9._-]+")


def build_safe_object_name(file_name: str) -> str:
    original_name = PurePath(file_name).name.strip()
    safe_name = SAFE_OBJECT_RE.sub("_", original_name) or "document"
    return f"{uuid4().hex}_{safe_name}"


def parse_storage_path(storage_path: str) -> tuple[str, str]:
    if not storage_path.startswith("s3://"):
        raise ValueError(f"Caminho de storage invalido: {storage_path}")

    path = storage_path.removeprefix("s3://")
    bucket, separator, object_name = path.partition("/")
    if not bucket or not separator or not object_name:
        raise ValueError(f"Caminho de storage invalido: {storage_path}")
    return bucket, object_name


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY.get_secret_value(),
            secure=settings.STORAGE_SECURE,
            http_client=urllib3.PoolManager(
                timeout=urllib3.Timeout(
                    connect=settings.STORAGE_CONNECT_TIMEOUT_SECONDS,
                    read=settings.STORAGE_READ_TIMEOUT_SECONDS,
                ),
                retries=urllib3.Retry(total=settings.STORAGE_MAX_RETRIES),
            ),
        )

    async def ensure_bucket_exists(self):
        await to_thread.run_sync(self._sync_ensure_bucket)

    async def is_available(self) -> bool:
        return await to_thread.run_sync(self.client.bucket_exists, settings.STORAGE_BUCKET_NAME)

    def _sync_ensure_bucket(self):
        if not self.client.bucket_exists(settings.STORAGE_BUCKET_NAME):
            self.client.make_bucket(settings.STORAGE_BUCKET_NAME)

    async def upload_file(self, file_name: str, file_data: bytes, content_type: str):
        object_name = build_safe_object_name(file_name)

        def _sync_upload():
            data_stream = io.BytesIO(file_data)
            return self.client.put_object(
                settings.STORAGE_BUCKET_NAME,
                object_name,
                data_stream,
                length=len(file_data),
                content_type=content_type,
            )

        await to_thread.run_sync(_sync_upload)
        return f"s3://{settings.STORAGE_BUCKET_NAME}/{object_name}"

    async def download_file(self, storage_path: str) -> bytes:
        bucket, object_name = parse_storage_path(storage_path)

        def _sync_download():
            response = self.client.get_object(bucket, object_name)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        return await to_thread.run_sync(_sync_download)


storage_service = StorageService()

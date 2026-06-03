from datetime import datetime
from typing import Literal

from pydantic import BaseModel

UploadJobStatus = Literal["pending", "processing", "completed", "failed", "canceled"]


class UploadJobResponse(BaseModel):
    job_id: str
    filename: str
    content_type: str
    file_size: int
    status: UploadJobStatus
    tenant_id: str
    error_message: str | None = None
    attempts: int
    max_attempts: int
    last_error: str | None = None
    document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str


class UploadResponse(UploadJobResponse):
    pass


class UploadJobListResponse(BaseModel):
    uploads: list[UploadJobResponse]
    limit: int
    offset: int
    count: int

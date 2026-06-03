from datetime import datetime
from typing import Literal

from pydantic import BaseModel

UploadJobStatus = Literal["pending", "processing", "completed", "failed"]


class UploadJobResponse(BaseModel):
    job_id: str
    filename: str
    content_type: str
    file_size: int
    status: UploadJobStatus
    tenant_id: str
    error_message: str | None = None
    document_id: str | None = None
    created_at: datetime
    updated_at: datetime
    message: str


class UploadResponse(UploadJobResponse):
    pass


class UploadJobListResponse(BaseModel):
    uploads: list[UploadJobResponse]

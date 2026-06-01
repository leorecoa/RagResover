from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_count: int
    message: str

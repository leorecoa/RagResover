from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatSource(BaseModel):
    index: int
    chunk_id: str
    document_id: str
    file_name: str
    score: float
    excerpt: str
    metadata: dict


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[ChatSource]

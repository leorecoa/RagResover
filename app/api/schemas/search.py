from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    file_name: str
    content: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]

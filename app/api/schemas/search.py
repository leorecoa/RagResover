from pydantic import BaseModel, Field

MetadataFilterValue = str | int | float | bool


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=-1.0, le=1.0)
    metadata_filters: dict[str, MetadataFilterValue] = Field(default_factory=dict)


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
    diagnostics: dict | None = None

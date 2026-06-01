from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    env: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    storage: str
    env: str
    version: str

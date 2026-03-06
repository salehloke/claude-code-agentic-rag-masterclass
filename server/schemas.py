from pydantic import BaseModel
from datetime import datetime


class Document(BaseModel):
    id: str
    filename: str
    file_path: str | None = None
    content_hash: str | None = None
    chunk_count: int = 0
    status: str = "pending"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    embedding: list[float] | None = None
    chunk_index: int
    token_count: int | None = None
    created_at: datetime | None = None

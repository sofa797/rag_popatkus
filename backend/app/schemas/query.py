from pydantic import BaseModel, field_serializer
from datetime import datetime
from typing import List, Dict, Any

class QueryRequest(BaseModel):
    query: str

class SourceMetadata(BaseModel):
    text: str
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceMetadata]

class HistoryItem(BaseModel):
    id: int
    query: str
    answer: str
    created_at: datetime
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        """Конвертирует datetime в ISO-строку для JSON"""
        return dt.isoformat()
    
    class Config:
        from_attributes = True

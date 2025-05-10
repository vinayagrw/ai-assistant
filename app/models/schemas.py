from pydantic import BaseModel
from typing import List, Optional

class Source(BaseModel):
    """Model for source information"""
    title: str
    url: Optional[str] = None
    content: str
    relevance_score: float

class QueryRequest(BaseModel):
    """Model for query request"""
    query: str

class QueryResponse(BaseModel):
    """Model for query response"""
    answer: str
    sources: List[Source]
    confidence_score: float
    used_internet_search: bool 
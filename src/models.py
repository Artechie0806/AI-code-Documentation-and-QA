# src/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any

class CodeFile(BaseModel):
    file_path: str
    language: str
    content: str
    file_hash: str
    loc: int

class CodeChunk(BaseModel):
    chunk_id: str
    chunk_type: str = Field(..., description="class, method, function, or module")
    file_path: str
    start_line: int
    end_line: int
    code: str
    # Metadata for context
    parent: Optional[str] = None
    imports: List[str] = []
    # We will fill this later with AI
    summary: Optional[str] = None
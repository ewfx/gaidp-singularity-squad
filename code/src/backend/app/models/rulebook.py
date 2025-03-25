from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class Rule(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    rule_id: str
    description: str
    condition: str
    severity: str  # HIGH, MEDIUM, LOW
    category: str
    created_at: datetime

class Rulebook(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    uuid: str
    rulebook_name: str
    description: str
    file_path: str
    created_at: datetime
    file_size: int
    original_filename: str
    rules: List[Rule] = []
    status: str = "PENDING"  # PENDING, PROCESSING, COMPLETED, FAILED
    processing_error: Optional[str] = None 
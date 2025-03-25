from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class Rule(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    column_name: str  # Name of the CSV column to validate
    description: str  # Description of the rule
    regex_pattern: str  # Regex pattern for validation

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
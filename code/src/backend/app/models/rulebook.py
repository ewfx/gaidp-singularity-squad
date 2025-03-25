from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Rulebook:
    uuid: str
    rulebook_name: str
    description: str
    file_path: str
    created_at: datetime
    file_size: int
    original_filename: str 
import os
from pathlib import Path

class Config:
    # Base directory of the project
    BASE_DIR = Path(__file__).parent.parent
    
    # Rulebooks storage directory
    RULEBOOKS_DIR = BASE_DIR / 'rulebooks'
    
    # Ensure rulebooks directory exists
    RULEBOOKS_DIR.mkdir(exist_ok=True)
    
    # Maximum file size (10 MB)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf'} 
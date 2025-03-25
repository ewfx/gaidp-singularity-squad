import uuid
import os
from datetime import datetime
from pathlib import Path
from flask import current_app
from ..models.rulebook import Rulebook
from ..utils.file_handler import save_rulebook_file, save_metadata, get_metadata

class RulebookService:
    @staticmethod
    def create_rulebook(file, rulebook_name, description):
        """Create a new rulebook entry"""
        rulebook_uuid = str(uuid.uuid4())
        file_path = save_rulebook_file(file, rulebook_uuid)
        
        metadata = {
            'uuid': rulebook_uuid,
            'rulebook_name': rulebook_name,
            'description': description,
            'file_path': file_path,
            'created_at': datetime.utcnow().isoformat(),
            'file_size': os.path.getsize(file_path),
            'original_filename': file.filename
        }
        
        save_metadata(metadata, rulebook_uuid)
        return metadata
    
    @staticmethod
    def get_rulebook(uuid):
        """Retrieve a rulebook by UUID"""
        return get_metadata(uuid)
    
    @staticmethod
    def get_all_rulebooks():
        """Retrieve all rulebooks"""
        rulebooks = []
        rulebooks_dir = Path(current_app.config['RULEBOOKS_DIR'])
        
        for uuid_dir in rulebooks_dir.iterdir():
            if uuid_dir.is_dir():
                metadata = get_metadata(uuid_dir.name)
                if metadata:
                    rulebooks.append(metadata)
        
        return rulebooks 
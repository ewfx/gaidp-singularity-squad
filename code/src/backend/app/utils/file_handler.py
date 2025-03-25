import os
import json
import magic
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

def is_pdf(file_stream):
    """Check if file is actually a PDF using python-magic"""
    mime = magic.from_buffer(file_stream.read(2048), mime=True)
    file_stream.seek(0)  # Reset file pointer
    return mime == 'application/pdf'

def save_rulebook_file(file, uuid):
    """Save the uploaded PDF file"""
    rulebook_dir = Path(current_app.config['RULEBOOKS_DIR']) / uuid
    rulebook_dir.mkdir(exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = rulebook_dir / filename
    file.save(str(file_path))
    
    return str(file_path)

def save_metadata(metadata, uuid):
    """Save metadata to JSON file"""
    rulebook_dir = Path(current_app.config['RULEBOOKS_DIR']) / uuid
    metadata_path = rulebook_dir / 'metadata.json'
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=4)

def get_metadata(uuid):
    """Retrieve metadata for a rulebook"""
    metadata_path = Path(current_app.config['RULEBOOKS_DIR']) / uuid / 'metadata.json'
    
    if not metadata_path.exists():
        return None
        
    with open(metadata_path, 'r') as f:
        return json.load(f) 
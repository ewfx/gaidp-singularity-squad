import uuid
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from flask import current_app
from ..models.rulebook import Rulebook, Rule
from ..utils.file_handler import save_rulebook_file, save_metadata, get_metadata
from .rule_generator_service import RuleGeneratorService
from ..config import Config
import pandas as pd
import google.generativeai as genai
from typing import List
import time
import pdfplumber

class RulebookService:
    def __init__(self):
        self.rule_generator = RuleGeneratorService()
        self.base_path = Config.UPLOAD_FOLDER
        os.makedirs(self.base_path, exist_ok=True)

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract relevant regulatory text from PDF file using pdfplumber"""
        try:
            relevant_text = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Get page dimensions
                    page_height = page.height
                    page_width = page.width
                    
                    # Extract text with word positions
                    words = page.extract_words(
                        keep_blank_chars=True,
                        use_text_flow=True,
                        horizontal_ltr=True,
                        vertical_ttb=True,
                        x_tolerance=3,
                        y_tolerance=3
                    )
                    
                    # Skip header and footer (typically 10% from top and bottom)
                    header_threshold = page_height * 0.1
                    footer_threshold = page_height * 0.9
                    
                    # Group words into lines
                    current_line = []
                    current_y = None
                    lines = []
                    
                    for word in words:
                        if current_y is None:
                            current_y = word['top']
                            current_line.append(word['text'])
                        elif abs(word['top'] - current_y) < 5:  # Same line
                            current_line.append(word['text'])
                        else:  # New line
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word['text']]
                            current_y = word['top']
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    # Filter and process lines
                    for line in lines:
                        # Skip empty lines
                        if not line.strip():
                            continue
                            
                        # Skip headers and footers
                        if any(word['top'] < header_threshold or word['top'] > footer_threshold 
                               for word in page.extract_words()):
                            continue
                            
                        # Skip page numbers and common header/footer text
                        if any(skip in line.lower() for skip in ['page', 'confidential', 'all rights reserved']):
                            continue
                            
                        # Skip lines that are too short (likely headers/footers)
                        if len(line.strip()) < 20:
                            continue
                            
                        # Skip lines that are too long (likely tables or formatting)
                        if len(line.strip()) > 200:
                            continue
                            
                        relevant_text.append(line.strip())
            
            # Join the filtered text
            extracted_text = '\n'.join(relevant_text)
            
            # Remove excessive whitespace and normalize line breaks
            extracted_text = '\n'.join(line for line in extracted_text.split('\n') if line.strip())
            
            # Remove common PDF artifacts
            extracted_text = extracted_text.replace('\x0c', '')  # Remove form feed characters
            extracted_text = ' '.join(extracted_text.split())  # Normalize whitespace
            
            return extracted_text
            
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    async def create_rulebook(self, file, rulebook_name: str, description: str) -> dict:
        """Create a new rulebook from uploaded PDF"""
        try:
            # Generate UUID for the rulebook
            rulebook_uuid = str(uuid.uuid4())
            rulebook_dir = os.path.join(self.base_path, rulebook_uuid)
            os.makedirs(rulebook_dir, exist_ok=True)
            
            # Save the uploaded file
            file_path = os.path.join(rulebook_dir, file.filename)
            file.save(file_path)
            
            # Create initial metadata
            metadata = {
                'uuid': rulebook_uuid,
                'rulebook_name': rulebook_name,
                'description': description,
                'file_path': file_path,
                'created_at': datetime.utcnow().isoformat(),
                'file_size': os.path.getsize(file_path),
                'original_filename': file.filename,
                'status': 'PROCESSING',
                'rules': []
            }
            
            # Save initial metadata
            metadata_path = os.path.join(rulebook_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, default=str)
            
            # Generate rules from the PDF
            try:
                # Generate rules directly from the PDF file
                rules = await self.rule_generator.generate_rules(file_path)
                
                # Update metadata with rules and status
                metadata['rules'] = [rule.dict() for rule in rules]
                metadata['status'] = 'COMPLETED'
                
                # Save updated metadata
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, default=str)
                
            except Exception as e:
                metadata['status'] = 'FAILED'
                metadata['processing_error'] = str(e)
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, default=str)
                raise
            
            return metadata
            
        except Exception as e:
            raise Exception(f"Error creating rulebook: {str(e)}")

    def get_rulebook(self, uuid: str) -> dict:
        """Get rulebook metadata by UUID"""
        try:
            metadata_path = os.path.join(self.base_path, uuid, 'metadata.json')
            if not os.path.exists(metadata_path):
                return None
            
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error retrieving rulebook: {str(e)}")

    def get_all_rulebooks(self) -> List[dict]:
        """Get all rulebooks"""
        try:
            rulebooks = []
            for uuid in os.listdir(self.base_path):
                rulebook = self.get_rulebook(uuid)
                if rulebook:
                    rulebooks.append(rulebook)
            return rulebooks
        except Exception as e:
            raise Exception(f"Error retrieving rulebooks: {str(e)}")

    def validate_transactions(self, csv_file, rulebook_uuid: str) -> List[dict]:
        """Validate transactions from CSV against a rulebook"""
        try:
            # Get rulebook
            rulebook = self.get_rulebook(rulebook_uuid)
            if not rulebook:
                raise ValueError(f"Rulebook with UUID {rulebook_uuid} not found")
            
            if rulebook['status'] != 'COMPLETED':
                raise ValueError(f"Rulebook {rulebook_uuid} is not ready for validation (status: {rulebook['status']})")
            
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Validate each transaction
            violations = []
            for _, transaction in df.iterrows():
                transaction_violations = self.rule_generator.validate_transaction(
                    transaction.to_dict(),
                    [Rule(**rule) for rule in rulebook['rules']]
                )
                if transaction_violations:
                    violations.append({
                        'transaction': transaction.to_dict(),
                        'violations': [rule.dict() for rule in transaction_violations]
                    })
            
            return violations
            
        except Exception as e:
            raise Exception(f"Error validating transactions: {str(e)}") 
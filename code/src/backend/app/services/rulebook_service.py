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
import logging
import re

class RulebookService:
    def __init__(self):
        self.base_path = Config.UPLOAD_FOLDER
        self.logger = logging.getLogger(__name__)
        self.rule_generator = RuleGeneratorService()
        self.logger.info(f"Initialized RulebookService with base path: {self.base_path}")

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

    def delete_rulebook(self, uuid: str) -> bool:
        """Delete a rulebook by UUID"""
        try:
            rulebook_dir = os.path.join(self.base_path, uuid)
            if not os.path.exists(rulebook_dir):
                return False
            
            # Remove all files in the directory
            for file in os.listdir(rulebook_dir):
                file_path = os.path.join(rulebook_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    self.logger.error(f"Error deleting file {file_path}: {str(e)}")
            
            # Remove the directory itself
            os.rmdir(rulebook_dir)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting rulebook {uuid}: {str(e)}")
            raise Exception(f"Error deleting rulebook: {str(e)}")

    def validate_transactions(self, csv_file, rulebook_id):
        """Validate transactions from CSV against rulebook rules"""
        try:
            # Get rulebook
            rulebook = self.get_rulebook(rulebook_id)
            if not rulebook:
                raise ValueError("Rulebook not found")
            
            if rulebook.get('status') != 'COMPLETED':
                raise ValueError("Rulebook is not ready for validation")
            
            # Read CSV file
            try:
                df = pd.read_csv(csv_file)
            except Exception as e:
                raise ValueError(f"Error reading CSV file: {str(e)}")
            
            # Initialize validation results
            validation_results = {
                'total_rows': len(df),
                'valid_rows': 0,
                'invalid_rows': 0,
                'row_validations': [],
                'column_validations': {},
                'summary': {
                    'total_columns': len(rulebook['rules']),
                    'columns_found': 0,
                    'columns_missing': 0,
                    'validation_stats': {}
                }
            }
            
            # Validate each row
            for index, row in df.iterrows():
                row_validation = {
                    'row_index': index + 1,
                    'row_data': row.to_dict(),
                    'column_validations': {},
                    'is_valid': True
                }
                
                # Validate each rule
                for rule in rulebook['rules']:
                    column = rule['column_name']
                    pattern = rule['regex_pattern']
                    
                    # Clean pattern (remove r"..." if present)
                    if pattern.startswith('r"') and pattern.endswith('"'):
                        pattern = pattern[2:-1]
                    
                    # Handle special cases
                    if pattern == '.*':
                        pattern = r'.*'  # Allow any characters
                    elif pattern == 'N/A':
                        pattern = r'.*'  # Allow any characters
                    elif pattern == 'XX':
                        pattern = r'.*'  # Allow any characters
                    elif pattern == '??':
                        pattern = r'.*'  # Allow any characters
                    elif pattern == 'invalid-date':
                        pattern = r'^\d{4}-\d{2}-\d{2}$'  # Standard date format
                    
                    # Initialize column validation stats if not exists
                    if column not in validation_results['column_validations']:
                        validation_results['column_validations'][column] = {
                            'pattern': pattern,
                            'description': rule['description'],
                            'valid_count': 0,
                            'invalid_count': 0,
                            'total_validations': 0
                        }
                    
                    # Check if column exists in CSV
                    if column not in row:
                        row_validation['column_validations'][column] = {
                            'is_valid': False,
                            'error': f"Column '{column}' not found in CSV"
                        }
                        row_validation['is_valid'] = False
                        continue
                    
                    # Update column found count
                    if index == 0:
                        validation_results['summary']['columns_found'] += 1
                    
                    # Get value and validate
                    value = str(row[column])
                    validation_results['column_validations'][column]['total_validations'] += 1
                    
                    try:
                        # Handle empty values
                        if pd.isna(value) or value.strip() == '':
                            is_valid = True  # Empty values are considered valid
                        else:
                            is_valid = bool(re.fullmatch(pattern, value))
                        
                        row_validation['column_validations'][column] = {
                            'is_valid': is_valid,
                            'value': value,
                            'pattern': pattern
                        }
                        
                        if is_valid:
                            validation_results['column_validations'][column]['valid_count'] += 1
                        else:
                            validation_results['column_validations'][column]['invalid_count'] += 1
                            row_validation['is_valid'] = False
                            row_validation['column_validations'][column]['error'] = f"Value '{value}' does not match pattern '{pattern}'"
                            
                    except re.error as e:
                        row_validation['column_validations'][column] = {
                            'is_valid': False,
                            'error': f"Invalid regex pattern: {str(e)}"
                        }
                        row_validation['is_valid'] = False
                
                # Update row counts
                if row_validation['is_valid']:
                    validation_results['valid_rows'] += 1
                else:
                    validation_results['invalid_rows'] += 1
                
                validation_results['row_validations'].append(row_validation)
            
            # Calculate missing columns
            validation_results['summary']['columns_missing'] = (
                validation_results['summary']['total_columns'] - 
                validation_results['summary']['columns_found']
            )
            
            return validation_results
            
        except ValueError as e:
            current_app.logger.error(f"Validation error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            current_app.logger.error(f"Unexpected error during validation: {str(e)}")
            raise ValueError(f"Error validating transactions: {str(e)}")

    def create_rulebook_sync(self, file, rulebook_name, description):
        """Create a new rulebook synchronously"""
        try:
            # Generate UUID
            rulebook_uuid = str(uuid.uuid4())
            self.logger.info(f"Creating new rulebook with UUID: {rulebook_uuid}")
            
            # Create directory for rulebook
            rulebook_dir = os.path.join(self.base_path, rulebook_uuid)
            os.makedirs(rulebook_dir, exist_ok=True)
            self.logger.info(f"Created rulebook directory: {rulebook_dir}")
            
            # Save uploaded file
            file_path = os.path.join(rulebook_dir, file.filename)
            file.save(file_path)
            self.logger.info(f"Saved uploaded file to: {file_path}")
            
            # Create initial metadata
            metadata = {
                'uuid': rulebook_uuid,
                'rulebook_name': rulebook_name,
                'description': description,
                'file_path': file_path,
                'created_at': datetime.now(),
                'file_size': os.path.getsize(file_path),
                'original_filename': file.filename,
                'status': 'PROCESSING'
            }
            
            # Save initial metadata
            metadata_path = os.path.join(rulebook_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, default=str)
            self.logger.info(f"Saved initial metadata to: {metadata_path}")
            
            try:
                # Generate rules from PDF
                self.logger.info("Starting rule generation from PDF")
                rules = self.rule_generator.generate_rules_sync(file_path)
                self.logger.info(f"Generated {len(rules)} rules from PDF")
                
                # Update metadata with generated rules
                metadata['rules'] = rules
                metadata['status'] = 'COMPLETED'
                
                # Save updated metadata
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, default=str)
                self.logger.info("Updated metadata with generated rules")
                
                return metadata
                
            except Exception as e:
                self.logger.error(f"Error during rule generation: {str(e)}")
                metadata['status'] = 'FAILED'
                metadata['processing_error'] = str(e)
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, default=str)
                raise Exception(f"Error generating rules: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error creating rulebook: {str(e)}")
            raise Exception(f"Error creating rulebook: {str(e)}") 
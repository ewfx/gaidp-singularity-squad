import os
from typing import List
from datetime import datetime
import google.generativeai as genai
from pydantic import BaseModel, ConfigDict
from ..models.rulebook import Rule, Rulebook
from ..config import Config
import asyncio
import json
import re
import io
import yaml
import logging

class RuleGeneratorService:
    def __init__(self):
        # Configure Google API
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.logger = logging.getLogger(__name__)

    async def generate_rules(self, pdf_path: str) -> List[Rule]:
        """Generate rules from PDF using Gemini"""
        try:
            # Read the PDF file
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Create a file-like object
            pdf_io = io.BytesIO(pdf_content)
            
            # Define the prompt
            prompt = """Analyze this regulatory document and extract ALL rules in the following YAML format:
rules:
  - column_name: name_of_csv_column
    description: clear description of the rule
    regex_pattern: valid python regex pattern

Guidelines:
1. Extract ALL rules from the document
2. column_name must be a valid CSV column name (no spaces, use underscores)
3. description should be clear and concise
4. regex_pattern must be a valid Python regex pattern that:
   - For numbers: r"^\\d+$" or r"^\\d{1,3}(,\\d{3})*(\\.\\d{2})?$"
   - For dates: r"^\\d{4}-\\d{2}-\\d{2}$"
   - For text: r"(?i).*required.*"
   - For currency: r"^\\$?\\d{1,3}(,\\d{3})*(\\.\\d{2})?$"
   - For percentages: r"^\\d+(\\.\\d+)?%$"
   - For email: r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
   - For phone: r"^\\+?\\d{10,15}$"

Example rules:
rules:
  - column_name: total_assets
    description: Total assets must be at least $100 billion
    regex_pattern: ^\\d+$
  - column_name: submission_date
    description: Report must be submitted by the specified date
    regex_pattern: ^\\d{4}-\\d{2}-\\d{2}$
  - column_name: report_type
    description: Report must be submitted via Reporting Central
    regex_pattern: (?i).*reporting\\s+central.*

Return ONLY the YAML structure, nothing else."""

            # Generate content
            model = genai.GenerativeModel('gemini-1.5-flash')
            parts = [
                {'text': prompt},
                {'inline_data': {'mime_type': 'application/pdf', 'data': pdf_content}}
            ]
            response = await model.generate_content_async(
                parts,
                request_options={"timeout": 600}  # Set timeout to 10 minutes
            )
            
            # Log the raw response for debugging
            self.logger.info(f"Raw response from LLM: {response.text}")
            
            # Clean the response by removing markdown code block markers
            cleaned_response = response.text.strip()
            if cleaned_response.startswith('```yaml'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Try to parse as YAML first
            try:
                rules_data = yaml.safe_load(cleaned_response)
                if not rules_data or 'rules' not in rules_data:
                    raise ValueError("No valid YAML structure found in response")
                
                rules = []
                for rule_data in rules_data['rules']:
                    # Validate regex pattern before creating rule
                    try:
                        re.compile(rule_data['regex_pattern'])
                    except re.error as e:
                        self.logger.warning(f"Invalid regex pattern: {rule_data['regex_pattern']}")
                        continue
                        
                    rule = Rule(
                        column_name=rule_data['column_name'],
                        description=rule_data['description'],
                        regex_pattern=rule_data['regex_pattern']
                    )
                    rules.append(rule)
                
                return rules
                
            except yaml.YAMLError as e:
                self.logger.error(f"YAML parsing error: {str(e)}")
                # If YAML parsing fails, try to extract JSON
                try:
                    # Try to find JSON structure in the response
                    json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                    if json_match:
                        rules_data = json.loads(json_match.group())
                        if not rules_data or 'rules' not in rules_data:
                            raise ValueError("No valid JSON structure found in response")
                        
                        rules = []
                        for rule_data in rules_data['rules']:
                            try:
                                re.compile(rule_data['regex_pattern'])
                            except re.error as e:
                                self.logger.warning(f"Invalid regex pattern: {rule_data['regex_pattern']}")
                                continue
                                
                            rule = Rule(
                                column_name=rule_data['column_name'],
                                description=rule_data['description'],
                                regex_pattern=rule_data['regex_pattern']
                            )
                            rules.append(rule)
                        
                        return rules
                    else:
                        raise ValueError("No valid JSON or YAML structure found in response")
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse both YAML and JSON response: {str(e)}")
                except Exception as e:
                    raise ValueError(f"Error processing response: {str(e)}")
                
        except Exception as e:
            raise Exception(f"Error generating rules: {str(e)}")

    def validate_transaction(self, transaction: dict, rules: List[Rule]) -> List[Rule]:
        """Validate a single transaction against the rules"""
        violations = []
        for rule in rules:
            if not self._check_rule(transaction, rule):
                violations.append(rule)
        return violations

    def _check_rule(self, transaction: dict, rule: Rule) -> bool:
        """Check if a transaction violates a specific rule using regex pattern"""
        try:
            pattern = re.compile(rule.regex_pattern, re.IGNORECASE)
            # Apply regex to the specific CSV column
            value = transaction.get(rule.column_name)
            if value is not None:
                if isinstance(value, str):
                    return bool(pattern.search(value))
                elif isinstance(value, (int, float)):
                    # For numeric values, convert to string for regex matching
                    return bool(pattern.search(str(value)))
            return False
        except re.error:
            # If regex pattern is invalid, consider it a violation
            return False 
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
import httpx

class RuleGeneratorService:
    def __init__(self):
        # Configure Google API
        genai.configure(api_key=Config.GOOGLE_API_KEY)

    async def generate_rules(self, pdf_path: str) -> List[Rule]:
        """Generate rules from PDF using Gemini"""
        try:
            # Read the PDF file
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Create a file-like object
            pdf_io = io.BytesIO(pdf_content)
            
            # Define the prompt
            prompt = """Analyze this regulatory document and extract rules in the following JSON format:
{
    "rules": [
        {
            "rule_id": "unique_id",
            "description": "rule description",
            "condition": "condition to check",
            "severity": "HIGH/MEDIUM/LOW",
            "category": "rule category"
        }
    ]
}

Guidelines:
1. Each rule must have a unique rule_id
2. Description should be clear and concise
3. Condition should be specific and testable
4. Severity must be one of: HIGH, MEDIUM, LOW
5. Category should reflect the regulatory domain (e.g., Capital Requirements, Risk Management, Reporting)

Return ONLY the JSON structure, nothing else."""

            # Generate content
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                contents=[
                    {
                        "mime_type": "application/pdf",
                        "data": pdf_content
                    },
                    prompt
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048
                ),
                request_options={"timeout": 600}  # Set timeout to 10 minutes
            )
            
            # Debug: Print the raw response
            print("Raw LLM Response:")
            print(response.text)
            
            # Extract JSON from markdown code block using regex
            json_regex = r"```json\s*(\{[\s\S]*?\})\s*```"
            match = re.search(json_regex, response.text)
            
            if not match:
                print("No JSON found in response. Full response:")
                print(response.text)
                raise Exception("No valid JSON structure found in the response")
            
            # Debug: Print the extracted JSON
            print("\nExtracted JSON:")
            print(match.group(1))
            
            # Parse the extracted JSON
            try:
                rules_data = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                print(f"\nJSON Parse Error: {str(e)}")
                print("Failed JSON content:")
                print(match.group(1))
                raise Exception(f"Failed to parse JSON from response: {str(e)}")
            
            # Convert to Rule objects
            rules = []
            for rule_data in rules_data.get('rules', []):
                try:
                    rule = Rule(
                        rule_id=rule_data['rule_id'],
                        description=rule_data['description'],
                        condition=rule_data['condition'],
                        severity=rule_data['severity'],
                        category=rule_data['category'],
                        created_at=datetime.utcnow().isoformat()  # Convert to ISO format string
                    )
                    rules.append(rule)
                except KeyError as e:
                    print(f"Warning: Missing required field in rule data: {str(e)}")
                    print("Rule data:", rule_data)
                    continue
            
            if not rules:
                raise Exception("No valid rules were generated from the text")
            
            return rules
            
        except Exception as e:
            print(f"\nError in generate_rules: {str(e)}")
            raise Exception(f"Error generating rules: {str(e)}")

    def validate_transaction(self, transaction: dict, rules: List[Rule]) -> List[Rule]:
        """Validate a single transaction against the rules"""
        violations = []
        for rule in rules:
            # Here you would implement the actual validation logic
            # This is a placeholder - you'll need to implement the actual validation
            # based on your specific rule conditions
            if not self._check_rule(transaction, rule):
                violations.append(rule)
        return violations

    def _check_rule(self, transaction: dict, rule: Rule) -> bool:
        """Check if a transaction violates a specific rule"""
        # This is a placeholder - implement actual validation logic
        # You might want to use a rule engine or custom validation logic
        return True 
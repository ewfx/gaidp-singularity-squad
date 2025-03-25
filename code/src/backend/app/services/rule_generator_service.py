import os
from typing import List
from datetime import datetime
import google.generativeai as genai
from pydantic import BaseModel, ConfigDict
from ..models.rulebook import Rule, Rulebook
from ..config import Config
import asyncio
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

class RuleGeneratorService:
    def __init__(self):
        # Configure Google API
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        
        # Initialize Gemini with LangChain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True,
            max_output_tokens=2048
        )
        
        # Define the output parser
        self.parser = PydanticOutputParser(pydantic_object=Rulebook)
        
        # Define the system prompt
        self.system_prompt = """You are a regulatory compliance expert. Analyze the provided regulatory document and extract key rules and requirements.
        For each rule, provide:
        1. A clear description of the rule
        2. The specific condition that must be met
        3. The severity level (HIGH, MEDIUM, LOW)
        4. The category of the rule (e.g., Capital Requirements, Risk Management, Reporting)
        
        Format the rules in a structured way that can be used for automated validation.
        Return the rules in JSON format with the following structure:
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
        }"""

        # Create the prompt template with proper variable handling
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input_text}")
        ])

    async def generate_rules(self, pdf_text: str) -> List[Rule]:
        """Generate rules from PDF text using Gemini"""
        try:
            # Create the chain
            chain = self.prompt | self.llm | self.parser
            
            # Generate rules with increased timeout
            result = await chain.ainvoke(
                {"input_text": pdf_text},  # Changed from 'text' to 'input_text' to match template
                config={
                    "run_name": "Generate Rules",
                    "request_options": {"timeout": 600}  # 10 minutes timeout
                }
            )
            
            # Add timestamps to rules
            for rule in result.rules:
                rule.created_at = datetime.utcnow()
            
            return result.rules
        except Exception as e:
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
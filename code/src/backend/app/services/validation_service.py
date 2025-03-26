import pandas as pd
import json
import re
from datetime import datetime

class ValidationService:
    def __init__(self):
        self.rulebooks = {}
        self.load_rulebooks()

    def load_rulebooks(self):
        """Load all available rulebooks."""
        try:
            # Example rulebooks - in production, these would be loaded from a database or files
            self.rulebooks = {
                "transaction_rulebook": {
                    "amount": {
                        "regex": r"^\d+(\.\d{1,2})?$",
                        "description": "Amount must be a valid number with up to 2 decimal places"
                    },
                    "transaction_id": {
                        "regex": r"^TXN-\d{6}$",
                        "description": "Transaction ID must be in format TXN-XXXXXX"
                    },
                    "email": {
                        "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                        "description": "Must be a valid email address"
                    },
                    "phone": {
                        "regex": r"^\+?1?\d{9,15}$",
                        "description": "Must be a valid phone number"
                    }
                },
                "customer_rulebook": {
                    "customer_id": {
                        "regex": r"^CUST-\d{6}$",
                        "description": "Customer ID must be in format CUST-XXXXXX"
                    },
                    "name": {
                        "regex": r"^[A-Za-z\s]{2,50}$",
                        "description": "Name must be 2-50 characters long, letters only"
                    },
                    "age": {
                        "regex": r"^\d{1,3}$",
                        "description": "Age must be a valid number"
                    }
                }
            }
        except Exception as e:
            print(f"Error loading rulebooks: {str(e)}")
            self.rulebooks = {}

    def get_rulebooks(self):
        """Get list of available rulebooks."""
        return list(self.rulebooks.keys())

    def validate_data(self, df, rulebook_name):
        """Validate DataFrame against selected rulebook."""
        if rulebook_name not in self.rulebooks:
            raise ValueError(f"Rulebook '{rulebook_name}' not found")

        rulebook = self.rulebooks[rulebook_name]
        validation_results = []
        total_rows = len(df)
        valid_rows = 0
        invalid_rows = 0

        for index, row in df.iterrows():
            row_results = {
                'row_index': index,
                'validation_errors': []
            }
            row_valid = True

            for column in df.columns:
                if column in rulebook:
                    value = str(row[column])
                    pattern = rulebook[column]['regex']
                    
                    if not re.match(pattern, value):
                        row_valid = False
                        row_results['validation_errors'].append({
                            'column': column,
                            'value': value,
                            'expected_pattern': pattern,
                            'description': rulebook[column]['description']
                        })

            if not row_valid:
                invalid_rows += 1
                validation_results.append(row_results)
            else:
                valid_rows += 1

        return {
            'validation_results': validation_results,
            'statistics': {
                'total_rows': total_rows,
                'valid_rows': valid_rows,
                'invalid_rows': invalid_rows,
                'validation_rate': (valid_rows / total_rows * 100) if total_rows > 0 else 0,
                'last_validated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    def get_column_validation_summary(self, validation_results):
        """Generate summary of validation errors by column."""
        column_summary = {}
        
        for result in validation_results['validation_results']:
            for error in result['validation_errors']:
                column = error['column']
                if column not in column_summary:
                    column_summary[column] = {
                        'error_count': 0,
                        'examples': []
                    }
                
                column_summary[column]['error_count'] += 1
                if len(column_summary[column]['examples']) < 3:  # Keep only 3 examples
                    column_summary[column]['examples'].append({
                        'value': error['value'],
                        'description': error['description']
                    })

        return column_summary 
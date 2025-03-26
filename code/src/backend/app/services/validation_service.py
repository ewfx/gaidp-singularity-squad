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

    def validate_data(self, csv_file, rulebook_id):
        """Validate CSV data against rulebook rules"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Get rulebook rules
            rulebook = self.get_rulebook(rulebook_id)
            if not rulebook:
                raise ValueError("Rulebook not found")
            
            # Initialize validation results
            validation_results = {
                "total_transactions": len(df),
                "violations": {
                    "total_rows": len(df),
                    "valid_rows": 0,
                    "invalid_rows": 0,
                    "row_validations": [],
                    "column_validations": {},
                    "summary": {
                        "total_columns": len(rulebook.get("rules", [])),
                        "columns_found": len(df.columns),
                        "columns_missing": 0,
                        "validation_stats": {}
                    },
                    "validation_rate": 0.0
                }
            }
            
            # Track column validation stats
            column_stats = {}
            
            # Validate each row
            for index, row in df.iterrows():
                row_validation = {
                    "row_index": index + 1,
                    "row_data": row.to_dict(),
                    "is_valid": True,
                    "errors": []
                }
                
                # Validate each column against rules
                for rule in rulebook.get("rules", []):
                    column = rule.get("column_name")
                    if column not in df.columns:
                        validation_results["violations"]["summary"]["columns_missing"] += 1
                        continue
                        
                    value = row.get(column)
                    pattern = rule.get("regex_pattern", "")
                    
                    # Clean pattern by removing r"..." format
                    pattern = pattern.replace('r"', '').replace('"', '')
                    
                    # Skip validation if value is empty
                    if pd.isna(value):
                        continue
                        
                    # Convert value to string for regex matching
                    value_str = str(value)
                    
                    try:
                        if not re.match(pattern, value_str):
                            row_validation["is_valid"] = False
                            row_validation["errors"].append({
                                "column": column,
                                "value": value_str,
                                "pattern": pattern,
                                "description": rule.get("description", "Invalid format")
                            })
                            
                            # Update column stats
                            if column not in column_stats:
                                column_stats[column] = {"valid": 0, "invalid": 0}
                            column_stats[column]["invalid"] += 1
                    except Exception as e:
                        row_validation["is_valid"] = False
                        row_validation["errors"].append({
                            "column": column,
                            "value": value_str,
                            "pattern": pattern,
                            "description": f"Validation error: {str(e)}"
                        })
                        
                        if column not in column_stats:
                            column_stats[column] = {"valid": 0, "invalid": 0}
                        column_stats[column]["invalid"] += 1
                
                # Update row validation stats
                if row_validation["is_valid"]:
                    validation_results["violations"]["valid_rows"] += 1
                else:
                    validation_results["violations"]["invalid_rows"] += 1
                
                validation_results["violations"]["row_validations"].append(row_validation)
            
            # Update column validations
            for column in df.columns:
                if column not in column_stats:
                    column_stats[column] = {"valid": 0, "invalid": 0}
                column_stats[column]["valid"] = validation_results["violations"]["valid_rows"]
                validation_results["violations"]["column_validations"][column] = column_stats[column]
            
            # Calculate validation rate
            total_rows = validation_results["violations"]["total_rows"]
            if total_rows > 0:
                validation_results["violations"]["validation_rate"] = round(
                    (validation_results["violations"]["valid_rows"] / total_rows) * 100, 2
                )
            
            # Convert NaN values to None or 0
            def clean_nan(obj):
                if isinstance(obj, dict):
                    return {k: clean_nan(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_nan(item) for item in obj]
                elif pd.isna(obj):
                    return None
                return obj
            
            validation_results = clean_nan(validation_results)
            
            return validation_results
            
        except Exception as e:
            raise ValueError(f"Validation error: {str(e)}")

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
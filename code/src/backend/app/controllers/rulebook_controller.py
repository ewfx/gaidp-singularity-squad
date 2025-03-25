from flask import request, send_file
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from ..services.rulebook_service import RulebookService
from ..utils.file_handler import is_pdf
import asyncio
import os
import uuid
from datetime import datetime
import json

# Create a custom JSON encoder
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create namespace with better description
api = Namespace(
    'rulebooks',
    description='Regulatory Rulebook Management API',
    path='/rulebooks'
)

# Define detailed response models with examples
rule_model = api.model('Rule', {
    'rule_id': fields.String(required=True, description='Unique identifier for the rule'),
    'description': fields.String(required=True, description='Description of the rule'),
    'condition': fields.String(required=True, description='Condition that must be met'),
    'severity': fields.String(required=True, description='Severity level (HIGH, MEDIUM, LOW)'),
    'category': fields.String(required=True, description='Category of the rule'),
    'created_at': fields.DateTime(required=True, description='When the rule was created')
})

rulebook_model = api.model('Rulebook', {
    'uuid': fields.String(required=True, description='Unique identifier for the rulebook'),
    'rulebook_name': fields.String(required=True, description='Name of the regulatory rulebook'),
    'description': fields.String(required=True, description='Detailed description of the rulebook'),
    'file_path': fields.String(required=True, description='Local path to the stored PDF file'),
    'created_at': fields.DateTime(required=True, description='Timestamp when the rulebook was uploaded'),
    'file_size': fields.Integer(required=True, description='Size of the PDF file in bytes'),
    'original_filename': fields.String(required=True, description='Original name of the uploaded file'),
    'rules': fields.List(fields.Nested(rule_model), description='Generated rules from the PDF'),
    'status': fields.String(required=True, description='Processing status (PENDING, PROCESSING, COMPLETED, FAILED)'),
    'processing_error': fields.String(description='Error message if processing failed')
})

# Define error response model with examples
error_model = api.model('Error', {
    'message': fields.String(required=True, description='Error message'),
    'code': fields.String(required=True, description='Error code'),
    'details': fields.Raw(description='Additional error details')
})

# Define upload parser with simplified requirements
upload_parser = api.parser()
upload_parser.add_argument(
    'file',
    location='files',
    type=FileStorage,
    required=True,
    help='PDF file containing regulatory rules (max 10MB)'
)
upload_parser.add_argument(
    'rulebook_name',
    location='form',
    type=str,
    required=True,
    help='Name of the regulatory rulebook (e.g., "Basel III", "MiFID II")'
)

# Define transaction validation parser
validation_parser = api.parser()
validation_parser.add_argument(
    'csv_file',
    location='files',
    type=FileStorage,
    required=True,
    help='CSV file containing transactions to validate'
)

# Initialize service
rulebook_service = RulebookService()

@api.route('/upload-pdf')
class RulebookUpload(Resource):
    @api.expect(upload_parser)
    @api.response(201, 'Rulebook created successfully', rulebook_model)
    @api.response(400, 'Invalid input', error_model)
    @api.response(413, 'File too large', error_model)
    @api.response(500, 'Server error', error_model)
    @api.doc(
        description='Upload a new regulatory rulebook PDF',
        responses={
            201: 'Rulebook successfully uploaded and processed',
            400: 'Invalid file format or missing required fields',
            413: 'File size exceeds maximum limit of 10MB',
            500: 'Internal server error during processing'
        }
    )
    def post(self):
        """Upload a new regulatory rulebook PDF file
        
        This endpoint accepts a PDF file containing regulatory rules along with the rulebook name.
        The backend will automatically:
        - Generate a unique UUID
        - Create a description based on the rulebook name
        - Store the file securely
        - Extract text from the PDF
        - Generate rules using LangChain and Gemini
        - Track metadata like file size and creation time
        
        The uploaded file must be:
        - A valid PDF file
        - Less than 10MB in size
        """
        args = upload_parser.parse_args()
        file = args['file']
        rulebook_name = args['rulebook_name']
        
        if not file:
            api.abort(400, "No file provided")
            
        if not is_pdf(file):
            api.abort(400, "File must be a PDF")
        
        try:
            # Generate a description based on the rulebook name
            description = f"Regulatory framework for {rulebook_name}"
            
            # Create rulebook
            rulebook = asyncio.run(rulebook_service.create_rulebook(file, rulebook_name, description))
            
            # Convert to dict and handle datetime serialization
            rulebook_dict = rulebook
            if isinstance(rulebook_dict['created_at'], datetime):
                rulebook_dict['created_at'] = rulebook_dict['created_at'].isoformat()
            for rule in rulebook_dict.get('rules', []):
                if 'created_at' in rule and isinstance(rule['created_at'], datetime):
                    rule['created_at'] = rule['created_at'].isoformat()
            
            return rulebook_dict, 201
        except Exception as e:
            api.abort(500, f"Error creating rulebook: {str(e)}")

@api.route('/rulebook/<string:uuid>')
@api.param('uuid', 'The unique identifier of the rulebook')
class RulebookResource(Resource):
    @api.response(200, 'Success', rulebook_model)
    @api.response(404, 'Rulebook not found', error_model)
    @api.doc(
        description='Retrieve metadata for a specific rulebook',
        responses={
            200: 'Rulebook metadata retrieved successfully',
            404: 'Rulebook with specified UUID not found'
        }
    )
    @api.marshal_with(rulebook_model)
    def get(self, uuid):
        """Get rulebook metadata by UUID"""
        rulebook = rulebook_service.get_rulebook(uuid)
        if not rulebook:
            api.abort(404, "Rulebook not found")
        
        # Convert to dict and handle datetime serialization
        rulebook_dict = rulebook
        rulebook_dict['created_at'] = rulebook_dict['created_at'].isoformat()
        for rule in rulebook_dict.get('rules', []):
            if 'created_at' in rule:
                rule['created_at'] = rule['created_at'].isoformat()
        
        return rulebook_dict

@api.route('/rulebooks')
class RulebookList(Resource):
    @api.response(200, 'Success', [rulebook_model])
    @api.doc(
        description='List all uploaded rulebooks',
        responses={
            200: 'List of all rulebooks retrieved successfully'
        }
    )
    @api.marshal_list_with(rulebook_model)
    def get(self):
        """List all uploaded rulebooks"""
        try:
            rulebooks = rulebook_service.get_all_rulebooks()
            return rulebooks
        except Exception as e:
            api.abort(500, message=str(e))

@api.route('/rulebook/<string:uuid>/validate')
@api.param('uuid', 'The unique identifier of the rulebook')
class TransactionValidation(Resource):
    @api.expect(validation_parser)
    @api.response(200, 'Validation completed successfully')
    @api.response(400, 'Invalid input', error_model)
    @api.response(404, 'Rulebook not found', error_model)
    @api.doc(
        description='Validate transactions from CSV against a rulebook',
        responses={
            200: 'Validation completed successfully',
            400: 'Invalid CSV file or rulebook not ready',
            404: 'Rulebook not found'
        }
    )
    def post(self, uuid):
        """Validate transactions from CSV against a rulebook
        
        This endpoint accepts a CSV file containing transactions and validates them
        against the rules generated from the specified rulebook.
        
        The CSV file must contain columns that match the rule conditions.
        """
        args = validation_parser.parse_args()
        csv_file = args['csv_file']
        
        if not csv_file:
            api.abort(400, "No CSV file provided")
        
        try:
            violations = rulebook_service.validate_transactions(csv_file, uuid)
            return {
                'total_transactions': len(violations),
                'violations': violations
            }
        except ValueError as e:
            api.abort(400, str(e))
        except Exception as e:
            api.abort(500, f"Error validating transactions: {str(e)}") 
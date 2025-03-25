from flask import request, send_file
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from ..services.rulebook_service import RulebookService
from ..utils.file_handler import is_pdf

# Create namespace with better description
api = Namespace(
    'rulebooks',
    description='Regulatory Rulebook Management API',
    path='/rulebooks'
)

# Define detailed response models with examples
rulebook_model = api.model('Rulebook', {
    'uuid': fields.String(required=True, description='Unique identifier for the rulebook', example='550e8400-e29b-41d4-a716-446655440000'),
    'rulebook_name': fields.String(required=True, description='Name of the regulatory rulebook', example='Basel III'),
    'description': fields.String(required=True, description='Detailed description of the rulebook', example='Basel III regulatory framework for banking supervision'),
    'file_path': fields.String(required=True, description='Local path to the stored PDF file', example='/rulebooks/550e8400-e29b-41d4-a716-446655440000/basel_iii.pdf'),
    'created_at': fields.DateTime(required=True, description='Timestamp when the rulebook was uploaded', example='2024-03-25T10:30:00Z'),
    'file_size': fields.Integer(required=True, description='Size of the PDF file in bytes', example=1048576),
    'original_filename': fields.String(required=True, description='Original name of the uploaded file', example='basel_iii.pdf')
})

# Define error response model with examples
error_model = api.model('Error', {
    'message': fields.String(required=True, description='Error message', example='File must be a PDF'),
    'code': fields.String(required=True, description='Error code', example='INVALID_FILE_TYPE'),
    'details': fields.Raw(description='Additional error details', example={'allowed_types': ['pdf']})
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
        },
        examples={
            'success': {
                'value': {
                    'uuid': '550e8400-e29b-41d4-a716-446655440000',
                    'rulebook_name': 'Basel III',
                    'description': 'Basel III regulatory framework for banking supervision',
                    'file_path': '/rulebooks/550e8400-e29b-41d4-a716-446655440000/basel_iii.pdf',
                    'created_at': '2024-03-25T10:30:00Z',
                    'file_size': 1048576,
                    'original_filename': 'basel_iii.pdf'
                }
            },
            'error': {
                'value': {
                    'message': 'File must be a PDF',
                    'code': 'INVALID_FILE_TYPE',
                    'details': {'allowed_types': ['pdf']}
                }
            }
        }
    )
    def post(self):
        """Upload a new regulatory rulebook PDF file
        
        This endpoint accepts a PDF file containing regulatory rules along with the rulebook name.
        The backend will automatically:
        - Generate a unique UUID
        - Create a description based on the rulebook name
        - Store the file securely
        - Track metadata like file size and creation time
        
        The uploaded file must be:
        - A valid PDF file
        - Less than 10MB in size
        
        Example request:
        ```
        curl -X POST http://localhost:5000/rulebooks/upload-pdf \
          -F "file=@basel_iii.pdf" \
          -F "rulebook_name=Basel III"
        ```
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
            
            metadata = RulebookService.create_rulebook(
                file,
                rulebook_name,
                description
            )
            return metadata, 201
        except Exception as e:
            api.abort(500, f"Error creating rulebook: {str(e)}")

@api.route('/rulebook/<string:uuid>')
@api.param('uuid', 'The unique identifier of the rulebook', example='550e8400-e29b-41d4-a716-446655440000')
class RulebookResource(Resource):
    @api.response(200, 'Success', rulebook_model)
    @api.response(404, 'Rulebook not found', error_model)
    @api.doc(
        description='Retrieve metadata for a specific rulebook',
        responses={
            200: 'Rulebook metadata retrieved successfully',
            404: 'Rulebook with specified UUID not found'
        },
        examples={
            'success': {
                'value': {
                    'uuid': '550e8400-e29b-41d4-a716-446655440000',
                    'rulebook_name': 'Basel III',
                    'description': 'Basel III regulatory framework for banking supervision',
                    'file_path': '/rulebooks/550e8400-e29b-41d4-a716-446655440000/basel_iii.pdf',
                    'created_at': '2024-03-25T10:30:00Z',
                    'file_size': 1048576,
                    'original_filename': 'basel_iii.pdf'
                }
            },
            'error': {
                'value': {
                    'message': 'Rulebook not found',
                    'code': 'NOT_FOUND',
                    'details': {'uuid': '550e8400-e29b-41d4-a716-446655440000'}
                }
            }
        }
    )
    @api.marshal_with(rulebook_model)
    def get(self, uuid):
        """Get rulebook metadata by UUID
        
        Retrieves the complete metadata for a specific rulebook using its unique identifier.
        This includes information such as name, description, file details, and creation timestamp.
        
        Example request:
        ```
        curl -X GET http://localhost:5000/rulebooks/rulebook/550e8400-e29b-41d4-a716-446655440000
        ```
        """
        rulebook = RulebookService.get_rulebook(uuid)
        if not rulebook:
            api.abort(404, "Rulebook not found")
        return rulebook

@api.route('/rulebooks')
class RulebookList(Resource):
    @api.response(200, 'Success', [rulebook_model])
    @api.doc(
        description='List all uploaded rulebooks',
        responses={
            200: 'List of all rulebooks retrieved successfully'
        },
        examples={
            'success': {
                'value': [
                    {
                        'uuid': '550e8400-e29b-41d4-a716-446655440000',
                        'rulebook_name': 'Basel III',
                        'description': 'Basel III regulatory framework for banking supervision',
                        'file_path': '/rulebooks/550e8400-e29b-41d4-a716-446655440000/basel_iii.pdf',
                        'created_at': '2024-03-25T10:30:00Z',
                        'file_size': 1048576,
                        'original_filename': 'basel_iii.pdf'
                    },
                    {
                        'uuid': '550e8400-e29b-41d4-a716-446655440001',
                        'rulebook_name': 'MiFID II',
                        'description': 'Markets in Financial Instruments Directive II',
                        'file_path': '/rulebooks/550e8400-e29b-41d4-a716-446655440001/mifid_ii.pdf',
                        'created_at': '2024-03-25T11:30:00Z',
                        'file_size': 2097152,
                        'original_filename': 'mifid_ii.pdf'
                    }
                ]
            }
        }
    )
    @api.marshal_list_with(rulebook_model)
    def get(self):
        """List all uploaded rulebooks
        
        Returns a comprehensive list of all rulebooks that have been uploaded to the system,
        including their metadata and basic information.
        
        Example request:
        ```
        curl -X GET http://localhost:5000/rulebooks/rulebooks
        ```
        """
        return RulebookService.get_all_rulebooks() 
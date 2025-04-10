from flask import Blueprint, render_template, request, jsonify
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import re
from datetime import datetime
from ..services.rulebook_service import RulebookService

# Create Blueprint for template rendering
validation_bp = Blueprint('validation', __name__)

# Create API namespace for REST endpoints
api = Namespace(
    'validation',
    description='Data Validation API',
    path='/validation'
)

# Initialize service
rulebook_service = RulebookService()

# Define upload parser
upload_parser = api.parser()
upload_parser.add_argument(
    'csv_file',
    location='files',
    type=FileStorage,
    required=True,
    help='CSV file to validate'
)

@validation_bp.route('/data-validation')
def data_validation_page():
    """Render the data validation page."""
    return render_template('data_validation.html')

@api.route('/validate/<string:rulebook_id>')
@api.param('rulebook_id', 'The unique identifier of the rulebook')
class ValidationResource(Resource):
    @api.expect(upload_parser)
    def post(self, rulebook_id):
        """Validate uploaded CSV file against selected rulebook."""
        try:
            # Get the uploaded file
            args = upload_parser.parse_args()
            csv_file = args['csv_file']

            if not csv_file:
                return jsonify({
                    'status': 'error',
                    'message': 'No file uploaded',
                    'data': None
                }), 400

            # Validate data using rulebook service
            validation_results = rulebook_service.validate_transactions(csv_file, rulebook_id)
            
            # Get total transactions from the CSV
            df = pd.read_csv(csv_file)
            total_transactions = len(df)
            
            # Format the response
            response_data = {
                'status': 'success',
                'message': 'Validation completed successfully',
                'data': {
                    'total_transactions': total_transactions,
                    'violations': validation_results
                }
            }
            
            return jsonify(response_data)
            
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': str(e),
                'data': None
            }), 400
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'An error occurred during validation: {str(e)}',
                'data': None
            }), 500 
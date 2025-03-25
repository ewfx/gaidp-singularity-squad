from flask import request, send_file
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from ..services.anomaly_service import AnomalyService
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
    'anomalyDetection',
    description='Anomaly Detection API',
    path='/anomalies'
)

# Define error response model with examples
error_model = api.model('Error', {
    'message': fields.String(required=True, description='Error message'),
    'code': fields.String(required=True, description='Error code'),
    'details': fields.Raw(description='Additional error details')
})

anomaly_model = api.model('Anomaly', {
    'transaction_id': fields.String(required=True, description='Unique identifier for the transaction'),
    'timestamp': fields.DateTime(required=True, description='Timestamp of the transaction'),
    'amount': fields.Float(required=True, description='Transaction amount'),
    'anomaly_label': fields.Integer(required=True, description='Anomaly label (1 for anomaly, 0 for normal)')
})

# Define upload parser with simplified requirements
upload_parser = api.parser()
upload_parser.add_argument(
    'transactions',
    location='files',
    type=FileStorage,
    required=True,
    help='CSV file containing transactions'
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
anomaly_service = AnomalyService()

@api.route('/get-anomalies')
class TransactionAssess(Resource):
    @api.expect(upload_parser)
    @api.response(201, 'Anomalies detected successfully', anomaly_model)
    @api.response(400, 'Invalid input', error_model)
    @api.response(413, 'File too large', error_model)
    @api.response(500, 'Server error', error_model)
    @api.doc(
        description='Upload a new transaction CSV',
        responses={
            201: 'Anomalies successfully detected',
            400: 'Invalid file format or missing required fields',
            413: 'File size exceeds maximum limit of 10MB',
            500: 'Internal server error during processing'
        }
    )
    def post(self):
        
        args = upload_parser.parse_args()
        file = args['transactions']
        
        if not file:
            api.abort(400, "No file provided")
        
        try:
            # Create rulebook
            anomalies=anomaly_service.predict_anomalies(file)
            
            return anomalies.to_string()
        except Exception as e:
            api.abort(500, f"Error detecting anomalies: {str(e)}")

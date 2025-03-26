from flask import request, send_file, Blueprint, render_template, jsonify
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from ..services.anomaly_service import AnomalyService
import asyncio
import os
import uuid
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np

# Create a custom JSON encoder
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create Blueprint for template rendering
anomaly_bp = Blueprint('anomaly', __name__)

# Create API namespace for REST endpoints
api = Namespace(
    'anomalies',
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

@anomaly_bp.route('/anomaly-detection')
def anomaly_detection_page():
    """Render the anomaly detection page."""
    return render_template('anomaly_detection.html')

@api.route('/get-anomalies')
class TransactionAssess(Resource):
    @api.expect(upload_parser)
    @api.response(200, 'Success', anomaly_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    @api.doc(
        description='Upload a new transaction CSV',
        responses={
            200: 'Anomalies successfully detected',
            400: 'Invalid file format or missing required fields',
            500: 'Internal server error during processing'
        }
    )
    def post(self):
        """Upload a CSV file and get anomaly detection results"""
        try:
            if 'transactions' not in request.files:
                api.abort(400, "No file uploaded")
            
            file = request.files['transactions']
            if file.filename == '':
                api.abort(400, "No file selected")
            
            if not file.filename.endswith('.csv'):
                api.abort(400, "File must be a CSV")
            
            # Save the file temporarily
            temp_path = f"/tmp/{file.filename}"
            file.save(temp_path)
            
            # Process the file
            result = anomaly_service.predict_anomalies(temp_path)
            
            # Clean up the temporary file
            os.remove(temp_path)
            
            # Return JSON response
            return result, 200
            
        except Exception as e:
            api.abort(500, f"Error detecting anomalies: {str(e)}")

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
class AnomalyDetectionResource(Resource):
    @api.expect(upload_parser)
    def post(self):
        """Process uploaded file and detect anomalies."""
        try:
            file = request.files['transactions']
            if not file:
                return {'error': 'No file uploaded'}, 400

            # Read CSV file
            df = pd.read_csv(file)
            
            # Process the data and detect anomalies
            processed_data = process_transactions(df)
            
            return jsonify({
                'status': 'success',
                'data': processed_data
            })
        except Exception as e:
            return {'error': str(e)}, 500

def process_transactions(df):
    """Process transaction data and detect anomalies."""
    # Basic data preprocessing
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # Calculate statistical measures for amount
    amount_mean = df['amount'].mean()
    amount_std = df['amount'].std()
    
    # Mark transactions as anomalous based on amount (example criterion)
    df['is_anomaly'] = (abs(df['amount'] - amount_mean) > 2 * amount_std).astype(int)
    
    # Prepare time series data
    time_series = prepare_time_series(df)
    
    # Prepare regional distribution
    regional_dist = prepare_regional_distribution(df)
    
    # Prepare transaction type analysis
    transaction_types = prepare_transaction_types(df)
    
    # Prepare detailed transaction data
    transactions = prepare_transaction_details(df)
    
    return {
        'time_series': time_series,
        'regional_distribution': regional_dist,
        'transaction_types': transaction_types,
        'transactions': transactions,
        'statistics': {
            'total_records': len(df),
            'anomaly_count': df['is_anomaly'].sum(),
            'detection_rate': (df['is_anomaly'].sum() / len(df) * 100),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }

def prepare_time_series(df):
    """Prepare time series data for visualization."""
    # Resample data to 5-minute intervals
    df_resampled = df.set_index('timestamp').resample('5T').agg({
        'is_anomaly': ['count', 'sum']
    }).fillna(0)
    
    return {
        'timestamps': df_resampled.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'normal_count': (df_resampled['is_anomaly']['count'] - df_resampled['is_anomaly']['sum']).tolist(),
        'anomaly_count': df_resampled['is_anomaly']['sum'].tolist()
    }

def prepare_regional_distribution(df):
    """Prepare regional distribution data."""
    regional_stats = df.groupby('region').agg({
        'is_anomaly': ['count', 'sum']
    }).fillna(0)
    
    return {
        'regions': regional_stats.index.tolist(),
        'total_transactions': regional_stats['is_anomaly']['count'].tolist(),
        'anomalies': regional_stats['is_anomaly']['sum'].tolist()
    }

def prepare_transaction_types(df):
    """Prepare transaction type analysis data."""
    type_stats = df.groupby('type').agg({
        'is_anomaly': ['count', 'sum']
    }).fillna(0)
    
    return {
        'types': type_stats.index.tolist(),
        'normal_count': (type_stats['is_anomaly']['count'] - type_stats['is_anomaly']['sum']).tolist(),
        'anomaly_count': type_stats['is_anomaly']['sum'].tolist()
    }

def prepare_transaction_details(df):
    """Prepare detailed transaction data for the table."""
    transactions = []
    
    for _, row in df.iterrows():
        risk_score = calculate_risk_score(row)
        transactions.append({
            'id': f"TXN-{row.name:06d}",
            'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'type': row['type'],
            'amount': f"${row['amount']:.2f}",
            'region': row['region'],
            'risk_score': f"{risk_score:.2f}",
            'status': 'Anomaly' if row['is_anomaly'] else 'Normal',
            'ip_address': row.get('ip_address', 'N/A'),
            'device_id': row.get('device_id', 'N/A'),
            'merchant': row.get('merchant', 'N/A'),
            'transaction_method': row.get('transaction_method', 'N/A'),
            'customer_id': row.get('customer_id', 'N/A'),
            'customer_since': row.get('customer_since', 'N/A'),
            'previous_transactions': row.get('previous_transactions', 0),
            'anomaly_factors': get_anomaly_factors(row, risk_score)
        })
    
    return transactions

def calculate_risk_score(transaction):
    """Calculate risk score for a transaction."""
    risk_score = 0.0
    
    # Base risk from anomaly detection
    if transaction['is_anomaly']:
        risk_score += 0.5
    
    # Additional risk factors
    amount_factor = min(transaction['amount'] / 10000, 0.3)  # Higher amounts increase risk
    risk_score += amount_factor
    
    # Add time-based risk (higher risk during non-business hours)
    hour = transaction['timestamp'].hour
    if hour < 6 or hour > 22:  # Outside 6 AM - 10 PM
        risk_score += 0.1
    
    return min(risk_score, 1.0)

def get_anomaly_factors(transaction, risk_score):
    """Get list of anomaly factors for a transaction."""
    factors = []
    
    if transaction['is_anomaly']:
        factors.append("Unusual transaction amount")
        
        # Time-based factors
        hour = transaction['timestamp'].hour
        if hour < 6 or hour > 22:
            factors.append("Transaction during non-business hours")
        
        # Amount-based factors
        if transaction['amount'] > 5000:
            factors.append("High-value transaction")
        
    return factors

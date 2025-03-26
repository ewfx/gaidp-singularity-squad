import uuid
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from flask import current_app
from ..models.rulebook import Rulebook, Rule
from ..utils.file_handler import save_rulebook_file, save_metadata, get_metadata
from .rule_generator_service import RuleGeneratorService
from ..config import Config
import pandas as pd
from typing import List
import time
import pdfplumber
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
        
class AnomalyService:
    def __init__(self):
        model_path = Path(__file__).parent / 'iso_model.pkl'
        with open(model_path, 'rb') as f:
            self.iso_model = pickle.load(f)

    def predict_anomalies(self, csv_file_path):
        """
        Predicts anomalies in a CSV file using the loaded Isolation Forest model.

        Args:
            csv_file_path: Path to the CSV file containing transaction data.

        Returns:
            A dictionary containing anomalies and visualization data
        """
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file_path)
            
            # Process numeric features for anomaly detection
            numeric_features = df.select_dtypes(include=[np.number]).columns
            df_model = df[numeric_features].dropna().copy()
            
            # Scale the features
            scaler = StandardScaler()
            X = scaler.fit_transform(df_model)
            
            # Predict anomalies
            iso_pred = np.where(self.iso_model.predict(X) == -1, 1, 0)
            iso_anomaly_pct = iso_pred.mean() * 100
            
            # Add anomaly labels to the original dataframe
            df['anomaly_label'] = 0
            df.loc[df_model.index, 'anomaly_label'] = iso_pred
            
            # Prepare visualization data
            time_series_data = self._prepare_time_series_data(df)
            regional_data = self._prepare_regional_data(df)
            transaction_types = self._prepare_transaction_types(df)
            
            # Calculate statistics
            stats = {
                'total_records': len(df),
                'anomaly_count': int(iso_pred.sum()),
                'detection_rate': float(iso_anomaly_pct),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Convert DataFrame to records, handling NaT and Timestamp values
            records = []
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    value = row[col]
                    if pd.isna(value):
                        record[col] = None
                    elif isinstance(value, pd.Timestamp):
                        record[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        record[col] = value
                records.append(record)
            
            # Prepare the response
            response = {
                'anomalies': records,
                'statistics': stats,
                'time_series': time_series_data,
                'regional_distribution': regional_data,
                'transaction_types': transaction_types
            }
            
            return response
            
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def _prepare_time_series_data(self, df):
        """Prepare time series data for visualization"""
        # Group by timestamp and count normal/anomalous transactions
        df['timestamp'] = pd.to_datetime(df['origination_date'], errors='coerce')
        # Drop rows with NaT values
        df = df.dropna(subset=['timestamp'])
        
        time_series = df.groupby('timestamp').agg({
            'anomaly_label': [
                ('normal_count', lambda x: (x == 0).sum()),
                ('anomaly_count', lambda x: (x == 1).sum())
            ]
        }).reset_index()
        
        # Flatten column names
        time_series.columns = ['timestamp', 'normal_count', 'anomaly_count']
        
        return {
            'timestamps': time_series['timestamp'].dt.strftime('%Y-%m-%d').tolist(),
            'normal_count': time_series['normal_count'].tolist(),
            'anomaly_count': time_series['anomaly_count'].tolist()
        }
    
    def _prepare_regional_data(self, df):
        """Prepare regional distribution data"""
        # Drop rows with NaT values in country
        df = df.dropna(subset=['country'])
        
        # Group by country and count total transactions and anomalies
        regional = df.groupby('country').agg({
            'anomaly_label': [
                ('total_transactions', 'count'),
                ('anomalies', lambda x: (x == 1).sum())
            ]
        }).reset_index()
        
        # Flatten column names
        regional.columns = ['country', 'total_transactions', 'anomalies']
        
        return {
            'regions': regional['country'].tolist(),
            'total_transactions': regional['total_transactions'].tolist(),
            'anomalies': regional['anomalies'].tolist()
        }
    
    def _prepare_transaction_types(self, df):
        """Prepare transaction type distribution data"""
        # Drop rows with NaT values in credit_facility_type
        df = df.dropna(subset=['credit_facility_type'])
        
        # Group by credit facility type and count normal/anomalous transactions
        type_dist = df.groupby('credit_facility_type').agg({
            'anomaly_label': [
                ('normal_count', lambda x: (x == 0).sum()),
                ('anomaly_count', lambda x: (x == 1).sum())
            ]
        }).reset_index()
        
        # Flatten column names
        type_dist.columns = ['credit_facility_type', 'normal_count', 'anomaly_count']
        
        return {
            'types': type_dist['credit_facility_type'].tolist(),
            'normal_count': type_dist['normal_count'].tolist(),
            'anomaly_count': type_dist['anomaly_count'].tolist()
        }

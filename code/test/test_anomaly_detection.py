import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from src.backend.app.services.anomaly_detection_service import AnomalyDetectionService
from src.backend.app.models.anomaly_detection_model import AnomalyDetectionModel
from src.backend.app.utils.data_processor import DataProcessor

class TestAnomalyDetection(unittest.TestCase):
    def setUp(self):
        """Set up test data and services"""
        self.anomaly_service = AnomalyDetectionService()
        self.data_processor = DataProcessor()
        self.model = AnomalyDetectionModel()
        
        # Create sample transaction data
        self.sample_data = pd.DataFrame({
            'customer_id': ['CUST001', 'CUST002', 'CUST003'],
            'internal_id': ['INT001', 'INT002', 'INT003'],
            'obligor_name': ['Company A', 'Company B', 'Company C'],
            'credit_facility_type': ['Term Loan', 'Revolving Credit', 'Term Loan'],
            'utilized_exposure_global': [1000000, 2000000, 3000000],
            'country': ['India', 'USA', 'UK'],
            'obligor_internal_risk_rating': ['A', 'B', 'C'],
            'anomaly_label': [0, 1, 0]
        })

    def test_data_processing(self):
        """Test data preprocessing functionality"""
        # Test data cleaning
        cleaned_data = self.data_processor.clean_data(self.sample_data)
        self.assertFalse(cleaned_data.isnull().any().any())
        
        # Test feature engineering
        processed_data = self.data_processor.process_features(cleaned_data)
        self.assertTrue('processed_amount' in processed_data.columns)
        
        # Test data validation
        validation_result = self.data_processor.validate_data(processed_data)
        self.assertTrue(validation_result['is_valid'])

    def test_anomaly_detection(self):
        """Test anomaly detection functionality"""
        # Test model prediction
        processed_data = self.data_processor.process_features(self.sample_data)
        predictions = self.model.predict(processed_data)
        self.assertEqual(len(predictions), len(self.sample_data))
        
        # Test anomaly scoring
        scores = self.model.get_anomaly_scores(processed_data)
        self.assertTrue(all(0 <= score <= 1 for score in scores))

    def test_statistics_calculation(self):
        """Test statistics calculation"""
        stats = self.anomaly_service.calculate_statistics(self.sample_data)
        
        # Test basic statistics
        self.assertEqual(stats['total_records'], 3)
        self.assertEqual(stats['anomaly_count'], 1)
        self.assertAlmostEqual(stats['detection_rate'], 33.33, places=2)
        
        # Test time series data
        self.assertTrue('time_series' in stats)
        self.assertTrue('timestamps' in stats['time_series'])
        self.assertTrue('normal_count' in stats['time_series'])
        self.assertTrue('anomaly_count' in stats['time_series'])

    def test_regional_distribution(self):
        """Test regional distribution calculation"""
        regional_data = self.anomaly_service.calculate_regional_distribution(self.sample_data)
        
        # Test regional data structure
        self.assertTrue('regions' in regional_data)
        self.assertTrue('total_transactions' in regional_data)
        self.assertTrue('anomalies' in regional_data)
        
        # Test data consistency
        self.assertEqual(len(regional_data['regions']), 3)  # India, USA, UK
        self.assertEqual(sum(regional_data['total_transactions']), 3)
        self.assertEqual(sum(regional_data['anomalies']), 1)

    def test_transaction_type_analysis(self):
        """Test transaction type analysis"""
        type_analysis = self.anomaly_service.analyze_transaction_types(self.sample_data)
        
        # Test analysis structure
        self.assertTrue('types' in type_analysis)
        self.assertTrue('normal_count' in type_analysis)
        self.assertTrue('anomaly_count' in type_analysis)
        
        # Test data consistency
        self.assertEqual(len(type_analysis['types']), 2)  # Term Loan and Revolving Credit
        self.assertEqual(sum(type_analysis['normal_count']), 2)
        self.assertEqual(sum(type_analysis['anomaly_count']), 1)

    def test_export_functionality(self):
        """Test export functionality"""
        # Test transaction details export
        transaction = self.sample_data.iloc[0].to_dict()
        export_data = self.anomaly_service.export_transaction_details(transaction)
        
        # Test export format
        self.assertTrue(isinstance(export_data, str))
        self.assertTrue('Transaction Details Export' in export_data)
        self.assertTrue('Basic Information' in export_data)
        self.assertTrue('Credit Facility Details' in export_data)

    def test_data_validation_rules(self):
        """Test data validation rules"""
        # Test amount validation
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, 'utilized_exposure_global'] = -1000
        validation_result = self.data_processor.validate_data(invalid_data)
        self.assertFalse(validation_result['is_valid'])
        
        # Test required fields validation
        missing_data = self.sample_data.copy()
        missing_data = missing_data.drop('customer_id', axis=1)
        validation_result = self.data_processor.validate_data(missing_data)
        self.assertFalse(validation_result['is_valid'])

    def test_risk_rating_analysis(self):
        """Test risk rating analysis"""
        risk_analysis = self.anomaly_service.analyze_risk_ratings(self.sample_data)
        
        # Test analysis structure
        self.assertTrue('ratings' in risk_analysis)
        self.assertTrue('counts' in risk_analysis)
        self.assertTrue('anomaly_counts' in risk_analysis)
        
        # Test data consistency
        self.assertEqual(len(risk_analysis['ratings']), 3)  # A, B, C
        self.assertEqual(sum(risk_analysis['counts']), 3)
        self.assertEqual(sum(risk_analysis['anomaly_counts']), 1)

if __name__ == '__main__':
    unittest.main() 
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
    def predict_anomalies(self,csv_file_path):
        """
        Predicts anomalies in a CSV file using the loaded Isolation Forest model.

        Args:
            csv_file_path: Path to the CSV file containing transaction data.

        Returns:
            A DataFrame with the original data and an 'anomaly_label' column
            indicating whether each record is an anomaly (1) or not (0).
        """

        df = pd.read_csv(csv_file_path)
        numeric_features = df.select_dtypes(include=[np.number]).columns
        df_model = df[numeric_features].dropna().copy()
        scaler = StandardScaler()
        X = scaler.fit_transform(df_model)

        iso_pred = np.where(self.iso_model.predict(X) == -1, 1, 0)
        iso_anomaly_pct = iso_pred.mean() * 100
        
        df['anomaly_label'] = 0  # Default to non-anomalous

        # Update only the rows that were used in prediction
        df.loc[df_model.index, 'anomaly_label'] = iso_pred
        
        print("Anomaly Detection Summary:")
        print(f"IsolationForest flagged {iso_anomaly_pct:.2f}% of records as anomalies.")
        return df

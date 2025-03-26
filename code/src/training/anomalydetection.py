import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.cluster import DBSCAN

# -----------------------------
# Step 1: Data Loading
# -----------------------------
data_path = "CorpLoanTransaction.csv"
df = pd.read_csv(data_path)

# -----------------------------
# Step 2: Feature Selection
# -----------------------------
# For anomaly detection, we select numeric features that represent key transaction parameters.
# You can modify this list as needed.
numeric_features = df.select_dtypes(include=[np.number]).columns

# Ensure no missing values in selected features
df_model = df[numeric_features].dropna().copy()

# -----------------------------
# Step 3: Data Preparation (Scaling)
# -----------------------------
scaler = StandardScaler()
X = scaler.fit_transform(df_model)

# -----------------------------
# Step 4: Anomaly Detection Models
# -----------------------------

# a) IsolationForest
iso_model = IsolationForest(contamination=0.15, random_state=42)
iso_model.fit(X)
# IsolationForest returns -1 for anomalies; convert them to 1 (anomaly) and 0 (normal)
iso_pred = np.where(iso_model.predict(X) == -1, 1, 0)
iso_anomaly_pct = iso_pred.mean() * 100


# -----------------------------
# Step 5: Results Comparison
# -----------------------------
print("Anomaly Detection Summary:")
print(f"IsolationForest flagged {iso_anomaly_pct:.2f}% of records as anomalies.")

# -----------------------------
# Step 6: Visualizing Decision Scores (if available)
# -----------------------------
# For IsolationForest, we can plot the decision_function scores.
try:
    iso_scores = iso_model.decision_function(X)
    plt.figure(figsize=(10, 6))
    plt.hist(iso_scores, bins=30, edgecolor='black', alpha=0.7)
    plt.title("IsolationForest Decision Function Score Distribution")
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()
except Exception as e:
    print("IsolationForest decision function not available:", e)

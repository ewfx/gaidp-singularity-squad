# 🕵️‍♂️ Unsupervised Anomaly Detection on Corporate Loan Transactions

This project identifies anomalous corporate loan transactions using **unsupervised machine learning**, specifically **Isolation Forest**. The focus is on detecting outliers that may represent fraud, data entry errors, or unusual financial patterns.

---

## 📊 Dataset

- **File**: `CorpLoanTransaction.csv`
- **Type**: Corporate loan transaction records
- **Features**: Numeric fields selected automatically
- **Missing Values**: Rows with nulls in selected features are dropped

---

## 🔄 Workflow

```mermaid
sequenceDiagram
    participant User
    participant Script
    participant Model
    participant Plot

    User->>Script: Load CorpLoanTransaction.csv
    Script->>Script: Select numeric features
    Script->>Script: Drop rows with missing values
    Script->>Script: Standardize features with StandardScaler
    Script->>Model: Train IsolationForest (15% contamination)
    Model-->>Script: Predict anomaly labels (0 = normal, 1 = anomaly)
    Script->>Script: Compute anomaly percentage
    Script->>User: Print anomaly summary
    Script->>Plot: Visualize decision function scores
```
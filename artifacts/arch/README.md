# RuleSense – Architectural Design Document

## Overview

**RuleSense** is a Generative AI–powered data profiling platform tailored for regulatory compliance in the financial domain. It automates the process of extracting validation rules from regulatory documents and applies these rules to transactional data for validation and anomaly detection.

The platform supports the complete pipeline:
1. Uploading a regulatory PDF to extract semantic rules.
2. Creating a structured rulebook in JSON.
3. Validating uploaded transactional CSVs against these rules.
4. Detecting anomalies using unsupervised ML techniques.
5. Presenting results through a Flask-based web interface.

---

## Architecture Diagram (High-Level)

```mermaid
graph TD

  %% User Interaction
  User[User Web Client] --> Flask[Flask API Server]

  %% API Endpoints
  Flask --> UploadPDF[POST /upload-pdf]
  Flask --> ValidateCSV[POST /validate-csv]
  Flask --> GetAnomalies[POST /get-anomalies]

  %% Rulebook Generation
  UploadPDF --> PDFParser[Extract PDF Text]
  PDFParser --> Gemini[Gemini AI API]
  Gemini --> Extractor[Extract Rule Sentences]
  Extractor --> RegexGen[Generate Regex Rules]
  RegexGen --> Rulebook[Save rulebook.json]

  %% CSV Validation
  ValidateCSV --> CSVReader1[Read Transaction CSV]
  CSVReader1 --> Rulebook
  Rulebook --> Validator[Apply Regex Rules]
  Validator --> ValidationReport[Generate Validation Report]

  %% Anomaly Detection
  GetAnomalies --> CSVReader2[Read Transaction CSV]
  CSVReader2 --> Scaler[Scale Numeric Features]
  Scaler --> IsolationForest[Isolation Forest]
  Scaler --> LOF[LOF / DBSCAN]
  IsolationForest --> AnomalyReport[Generate Anomaly Report]
  LOF --> AnomalyReport

  %% Storage
  Rulebook --> Storage[Local File Storage]
  ValidationReport --> Storage
  AnomalyReport --> Storage
```

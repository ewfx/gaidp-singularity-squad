# RuleSense: Gen AI-powered Data Profiling for Regulatory Reporting

## Table of Contents

- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)
- [Sample Dataset](#sample-dataset)
- [Regulatory Rules](#regulatory-rules)
- [Submission Deliverables](#submission-deliverables)

---

## Introduction

RuleSense is a Gen AI-powered compliance assistant designed to automate regulatory data profiling in the financial sector. It uses Gemini’s document processing capabilities and unsupervised machine learning models to extract rules from complex regulatory documents, validate transactional data, identify anomalies, assess risks, and recommend remediation actions.

---

## Demo

- Live Demo: [Link to Demo](#)
- Video Walkthrough: [Link to Video](#)

Screenshots:

- RuleSense 
  ![Rulebook Generator UI](artifacts/screenshots/homepage.jpeg)

- GenAI Rulebook Generator
  ![Rulebook Generator](artifacts/screenshots/rulebook1.jpeg)

- Regex Based Rulebooks
  ![Rulebooks](artifacts/screenshots/rulebook2.jpeg)
  
- Transactions Data Validator
  ![Transactions Validator](artifacts/screenshots/validation1.jpeg)
  
- Anomaly Patterns Detector in Transactions  
  ![Anomaly Detector](artifacts/screenshots/anamoly1.jpeg)

- Anomaly Detector  
  ![Anomaly Detector](artifacts/screenshots/anamoly2.jpeg)

---

## Inspiration

Financial institutions face a major challenge when translating regulatory reporting instructions into enforceable data rules. This manual and error-prone process often slows down compliance cycles. RuleSense was built to streamline this process by automatically interpreting regulations and applying intelligent validations.

---

## What It Does

- Extracts data validation rules from regulatory PDFs using Gemini AI
- Parses extracted rules into structured JSON format with regex
- Validates uploaded transactional CSVs against these rules
- Flags validation issues and suggests remediation actions
- Detects anomalies in data using unsupervised learning
- Implements a dynamic risk scoring system
- Enables audit-friendly, explainable insights for compliance teams

```mermaid
sequenceDiagram
    %% Participants with icons
    actor User as User <<fa-user>>
    participant UI as Flask HTML UI <<fa-chrome>>
    participant Backend as Flask Backend (API Layer) <<fa-cogs>>
    participant Gemini as Gemini AI API <<fa-robot>>
    participant RuleEngine as Rulebook Generator <<fa-book>>
    participant RegexParser as Regex Rule Parser <<fa-code>>
    participant CSVValidator as CSV Validation Engine <<fa-table>>
    participant AnomalyDetector as ML Anomaly Engine <<fa-chart-line>>
    participant JSONStore as Local JSON Rulebook <<fa-database>>

    %% PDF Upload & Rulebook Generation
    User->>UI: Upload regulatory PDF
    UI->>Backend: POST /generate-rulebook
    Backend->>Gemini: Send PDF content for processing
    Gemini-->>Backend: Extracted regulatory instructions
    Backend->>RuleEngine: Parse relevant rule sections
    RuleEngine->>RegexParser: Convert instructions to regex rules
    RegexParser-->>RuleEngine: Regex rules (field-wise)
    RuleEngine->>JSONStore: Save rulebook.json
    JSONStore-->>Backend: Confirmation
    Backend-->>UI: Display generated rulebook summary

    %% CSV Upload & Validation
    User->>UI: Upload CSV transactional file
    UI->>Backend: POST /validate-csv
    Backend->>JSONStore: Load rulebook.json
    Backend->>CSVValidator: Apply regex validations to CSV
    CSVValidator-->>Backend: Validation results (violations, matched rules)
    Backend-->>UI: Display validation results with rule references

    %% Anomaly Detection
    User->>UI: Click "Detect Anomalies"
    UI->>Backend: GET /detect-anomalies
    Backend->>CSVValidator: Preprocess numeric features
    CSVValidator->>AnomalyDetector: Send processed dataset
    AnomalyDetector-->>Backend: Anomaly labels and risk scores
    Backend-->>UI: Display anomaly summary and risk insights

    %% Remediation (Optional)
    Backend->>Backend: Generate remediation suggestions
    Backend-->>UI: Display automated recommendations

```

---

## How We Built It

**Regulatory Rulebook Extraction**

- PDF parsing using Gemini AI’s document processing API
- Semantic chunking and cosine similarity for relevant rule matching
- Regex-based pattern extraction and rulebook generation (JSON format)

**Validation Engine**

- CSV upload interface for transactional datasets
- Field-by-field regex validation using the generated rulebook
- Detailed output: matched rule ID, violation description, suggestion

**Anomaly Detection**

- Uses Isolation Forest, DBSCAN, and LOF from scikit-learn
- Scales numeric features with StandardScaler
- Visualizes anomaly distribution using matplotlib

**Frontend**

- Built using flask templates to allow document and CSV uploads, validation display, and anomaly review

```mermaid
flowchart TD
  subgraph Client
    Browser["Web Browser (User)"]
  end

  subgraph UI["Flask Frontend"]
    HTMLUI["HTML Templates (Jinja2)"]
  end

  subgraph WebServer["Flask Backend"]
    Flask["Flask App"]
    API["API Routes"]
  end

  subgraph RulebookEngine["Rulebook Generation Engine"]
    Gemini["Gemini AI (Regulatory PDF Processor)"]
    RegexParser["Custom Regex Rule Parser"]
    RulebookJSON["Generated Rulebook (JSON)"]
  end

  subgraph Validator["CSV Validation Engine"]
    CSVUpload["CSV Upload & Parser"]
    RuleValidator["Regex Validator"]
    ValidationResults["Validation Report"]
  end

  subgraph AnomalyDetector["Anomaly Detection Engine"]
    Scaler["StandardScaler"]
    IFModel["Isolation Forest"]
    LOFModel["LOF / DBSCAN"]
    MLReport["Anomaly Report"]
  end

  subgraph Storage["Local Storage"]
    LocalFS["Filesystem (uploads, rulebooks, logs)"]
  end

  %% UI & Routing
  Browser --> HTMLUI
  HTMLUI --> Flask
  Flask --> API

  %% Rulebook Creation Flow
  API --> Gemini
  Gemini --> RegexParser
  RegexParser --> RulebookJSON
  RulebookJSON --> LocalFS

  %% CSV Validation Flow
  API --> CSVUpload
  CSVUpload --> RuleValidator
  RulebookJSON --> RuleValidator
  RuleValidator --> ValidationResults
  ValidationResults --> LocalFS

  %% Anomaly Detection Flow
  RuleValidator --> Scaler
  Scaler --> IFModel
  Scaler --> LOFModel
  IFModel --> MLReport
  LOFModel --> MLReport
  MLReport --> LocalFS
```
---

## Challenges We Faced

- Parsing varied PDF structures and noisy formatting
- Extracting accurate regex patterns from natural language rules
- Balancing anomaly detection thresholds to avoid false positives
- Ensuring explanations are understandable by non-technical auditors
- Maintaining performance and scalability for large CSVs

---

## How to Run

#### Clone the repository
```bash
git clone [https://github.com/your-username/rulesense.git](https://github.com/ewfx/gaidp-singularity-squad.git)
cd gaidp-singularity-squad.git
```

#### Set up environment variables
```bash
cp code/src/backend/.env.example code/src/backend/.env
```

#### Edit .env and update with your Gemini API key:
```bash
GOOGLE_API_KEY=your_api_key_here
FLASK_ENV=development
FLASK_DEBUG=1
```

### Install Docker
 - Follow official instructions to install Docker and Docker Compose:
 - macOS/Linux: https://docs.docker.com/desktop/install/mac-install/
 - Windows: https://docs.docker.com/desktop/install/windows-install/


### Verify installation:

```bash
docker --version
docker compose version
```


### Build and run the application
##### macOS/Linux
```bash
docker compose up --build
```
##### Windows

```bash
docker-compose up --build
```

### Open the application
##### Once the container is running, go to:
```bash
http://localhost:5001
```

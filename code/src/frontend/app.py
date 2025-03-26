from flask import Flask, request, render_template, redirect, url_for
import os, uuid
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Dummy rules + dataset
df = pd.DataFrame({
    'CustomerID': [1, 2, 3],
    'LoanAmount': [50000, -1000, 200000],
    'CreditScore': [650, 300, 720]
})
rules = [
    {"column": "LoanAmount", "condition": ">= 0", "description": "Loan must be non-negative"},
    {"column": "CreditScore", "condition": ">= 500", "description": "Credit score must be >= 500"}
]

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template("upload.html")

    # POST — handle PDF
    file = request.files.get('pdf')
    if not file or file.filename == '':
        return "No file selected", 400

    filename = f"{uuid.uuid4()}.pdf"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Apply rules to dataset
    violations = []
    for rule in rules:
        col, cond = rule['column'], rule['condition']
        violating = df.query(f"{col} not {cond}")
        for _, row in violating.iterrows():
            violations.append({
                "CustomerID": row["CustomerID"],
                "Column": col,
                "Value": row[col],
                "Rule": rule["description"]
            })

    return render_template("results.html", violations=violations, rule_count=len(rules))


if __name__ == '__main__':
    app.run(debug=True)

import os
import json
import pandas as pd
import requests

# Constants
CDGC_API_URL = "https://your-cdgc-instance/api"
API_KEY = "your_api_key_here"

# File paths
RULES_DIRECTORY = "/mnt/data/"
EXCEL_FILE = "/mnt/data/PCI_DSS_Regualtion_Assets.xlsx"
DQ_OUTPUT_FILE = "/mnt/data/Generated_IDMC_DQ_Bundle.json"
BT_OUTPUT_FILE = "/mnt/data/Generated_Business_Terms.xlsx"

# Function to upload data to CDGC API
def upload_to_cdgc(data, endpoint):
    headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    response = requests.post(f"{CDGC_API_URL}/{endpoint}", json=data, headers=headers)
    if response.status_code == 200:
        print(f"Successfully uploaded to {endpoint}")
    else:
        print(f"Upload failed with status code {response.status_code}: {response.text}")

# Load Business Terms and Classification from the Excel file
def load_business_terms(file_path):
    df = pd.read_excel(file_path, sheet_name="Business Terms")
    business_terms = []
    
    for _, row in df.iterrows():
        term_entry = {
            "Reference ID": f"BT_{row['Business Term']}",
            "Name": row['Business Term'],
            "Description": row['Definition'],
            "Alias Names": row.get('Alias Names', ""),
            "Business Logic": row.get('Business Logic', ""),
            "Critical Data Element": row.get('Critical Data Element', "No"),
            "Examples": row.get('Examples', ""),
            "Format Type": row.get('Format Type', ""),
            "Format Description": row.get('Format Description', ""),
            "Lifecycle": row.get('Lifecycle', ""),
            "Security Level": row.get('Security Level', ""),
            "Classifications": row.get('Classification', ""),
            "Operation": "Create",
            "Parent: Subdomain": row.get('Parent: Subdomain', ""),
            "Parent: Business Term": row.get('Parent: Business Term', ""),
            "Parent: Metric": row.get('Parent: Metric', ""),
            "Parent: Domain": row.get('Parent: Domain', "")
        }
        business_terms.append(term_entry)
    
    return business_terms

# Load Data Quality rules from the Excel file
def load_dq_rules_from_excel(file_path):
    df = pd.read_excel(file_path, sheet_name="Data Quality")
    dq_rules = []
    
    for _, row in df.iterrows():
        rule_entry = {
            "id": f"DQ_{row['Column Name']}",
            "name": row['Rule Name'],
            "description": row['Rule Description'],
            "documentType": "RULE_SPECIFICATION",
            "dimension": row.get('Dimension', ""),
            "exception": "false",
            "inputFields": [row['Column Name']],
            "ruleLogic": row.get('Rule Logic', "")
        }
        dq_rules.append(rule_entry)
    
    return dq_rules

# Load and process rule files from directory
def process_dq_rules(directory):
    dq_rules = []
    
    for filename in os.listdir(directory):
        if filename.endswith(".RULE_SPECIFICATION.json"):
            file_path = os.path.join(directory, filename)
            
            with open(file_path, "r") as file:
                rule_data = json.load(file)
                
                rule_entry = {
                    "id": rule_data.get("id", ""),
                    "name": rule_data.get("name", ""),
                    "description": rule_data.get("description", ""),
                    "documentType": rule_data.get("documentType", "RULE_SPECIFICATION"),
                    "dimension": next((attr["value"] for attr in rule_data.get("customAttributes", {}).get("stringAttrs", []) if attr["name"] == "DIMENSION"), ""),
                    "exception": next((attr["value"] for attr in rule_data.get("customAttributes", {}).get("stringAttrs", []) if attr["name"] == "EXCEPTION"), "false"),
                    "inputFields": [field["name"] for field in json.loads(rule_data.get("nativeData", {}).get("documentBlob", "{}")).get("inputFields", [])],
                    "ruleLogic": json.loads(rule_data.get("nativeData", {}).get("documentBlob", "{}")).get("ruleModel", "")
                }
                
                dq_rules.append(rule_entry)
    
    return dq_rules

# Combine business terms, classifications, and DQ rules
business_terms = load_business_terms(EXCEL_FILE)
dq_rules_from_excel = load_dq_rules_from_excel(EXCEL_FILE)
dq_rules_from_directory = process_dq_rules(RULES_DIRECTORY)

# Generate Informatica-compatible DQ bundle
dq_bundle = {
    "bundleName": "PCI_DSS_DQ_Bundle",
    "rules": dq_rules_from_excel + dq_rules_from_directory
}

# Save outputs
pd.DataFrame(business_terms).to_excel(BT_OUTPUT_FILE, index=False)
with open(DQ_OUTPUT_FILE, "w") as output_file:
    json.dump(dq_bundle, output_file, indent=4)

print(f"Generated Business Terms Excel: {BT_OUTPUT_FILE}")
print(f"Generated Informatica-compatible JSON bundle: {DQ_OUTPUT_FILE}")

# Upload to CDGC API
upload_to_cdgc(business_terms, "business-terms")
upload_to_cdgc(dq_bundle, "data-quality-rules")

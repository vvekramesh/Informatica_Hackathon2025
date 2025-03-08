import os
import json
import pandas as pd
import requests

# Constants
CDGC_API_URL = "https://your-cdgc-instance/v1"
CDGC_AUTH_URL = "https://your-cdgc-instance/v1/login"
USERNAME = "your_username"
PASSWORD = "your_password"

# File paths
RULES_DIRECTORY = "/mnt/data/"
EXCEL_FILE = "/mnt/data/PCI_DSS_Regualtion_Assets.xlsx"
DQ_OUTPUT_FILE = "/mnt/data/Generated_IDMC_DQ_Bundle.json"
BT_OUTPUT_FILE = "/mnt/data/Generated_Business_Terms.xlsx"

# Authenticate and get access token
def get_access_token():
    payload = {"username": USERNAME, "password": PASSWORD}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(CDGC_AUTH_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Authentication failed: {response.text}")

# Function to upload data to CDGC API
def upload_to_cdgc(data, endpoint, token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    url = f"{CDGC_API_URL}/{endpoint}"
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code in [200, 201]:
        print(f"Successfully uploaded to {endpoint}")
    else:
        print(f"Upload failed with status code {response.status_code}: {response.text}")

# Load Business Terms and Classification from the Excel file
def load_business_terms(file_path):
    df = pd.read_excel(file_path, sheet_name="Business Terms")
    business_terms = []
    
    for _, row in df.iterrows():
        term_entry = {
            "name": row['Business Term'],
            "description": row['Definition'],
            "classifications": row.get('Classification', ""),
            "aliasNames": row.get('Alias Names', ""),
            "businessLogic": row.get('Business Logic', ""),
            "securityLevel": row.get('Security Level', ""),
            "lifecycle": row.get('Lifecycle', ""),
            "parentDomain": row.get('Parent: Domain', ""),
            "parentSubdomain": row.get('Parent: Subdomain', ""),
            "parentBusinessTerm": row.get('Parent: Business Term', "")
        }
        business_terms.append(term_entry)
    
    return business_terms

# Load Data Quality rules from the Excel file
def load_dq_rules_from_excel(file_path):
    df = pd.read_excel(file_path, sheet_name="Data Quality")
    dq_rules = []
    
    for _, row in df.iterrows():
        rule_entry = {
            "name": row['Rule Name'],
            "description": row['Rule Description'],
            "dimension": row.get('Dimension', ""),
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
                    "name": rule_data.get("name", ""),
                    "description": rule_data.get("description", ""),
                    "dimension": next((attr["value"] for attr in rule_data.get("customAttributes", {}).get("stringAttrs", []) if attr["name"] == "DIMENSION"), ""),
                    "inputFields": [field["name"] for field in json.loads(rule_data.get("nativeData", {}).get("documentBlob", "{}")).get("inputFields", [])],
                    "ruleLogic": json.loads(rule_data.get("nativeData", {}).get("documentBlob", "{}")).get("ruleModel", "")
                }
                
                dq_rules.append(rule_entry)
    
    return dq_rules

# Authenticate and get token
token = get_access_token()

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
upload_to_cdgc({"businessTerms": business_terms}, "assets/business-terms/import", token)
upload_to_cdgc({"rules": dq_bundle["rules"]}, "assets/data-quality-rules/import", token)

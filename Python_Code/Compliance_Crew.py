import pandas as pd
import requests

# Constants for CDGC API
CDGC_API_URL = "https://your-cdgc-instance/api"
API_KEY = "your_api_key_here"

# Load the Excel file with multiple sheets
file_path = "/mnt/data/PCI_DSS_Regualtion_Assets.xlsx"
xls = pd.ExcelFile(file_path)

# Assume the default (first) sheet contains PCI DSS rules
df_rules = pd.read_excel(xls, sheet_name=0)

# Try loading the Business Terms sheet (if it exists)
try:
    df_bterm = pd.read_excel(xls, sheet_name="Business Terms")
except Exception as e:
    print("Business Terms sheet not found. Proceeding without it.")
    df_bterm = pd.DataFrame()

# If the Business Terms sheet exists, merge it with the PCI DSS rules based on a common key.
# Here we assume both sheets have a column named 'column name'. Adjust as necessary.
if not df_bterm.empty:
    merged_df = pd.merge(df_rules, df_bterm, on="column name", how="left", suffixes=("", "_bt"))
else:
    merged_df = df_rules

# Define the output template columns (Informatica-compatible)
output_columns = [
    "Reference ID", "Name", "Description", "Alias Names", "Business Logic", "Critical Data Element", "Examples",
    "Format Type", "Format Description", "Lifecycle", "Security Level", "Classifications", "Operation",
    "Parent: Subdomain", "Parent: Business Term", "Parent: Metric", "Parent: Domain"
]

def generate_pci_dss_classifications(df):
    output_data = []
    for _, row in df.iterrows():
        # Process only rows marked as PCI (assumes 'is PCI' is set to 'X' for PCI data)
        if row.get('is PCI') == 'X':
            # Default values based on the rules sheet
            name = row.get('column name', '')
            default_description = f"Sensitive PCI DSS data related to {name}"
            # If available, override with values from the business term sheet
            business_term = row.get('Business Term', None)  # assumed column from Business Terms sheet
            description = row.get('Business Description', default_description)
            alias_names = row.get('Alias Names', "")
            business_logic = row.get('Business Logic', "Data classified as PCI DSS regulated.")
            examples = row.get('Examples', "")
            format_type = row.get('Format Type', "String")
            format_description = row.get('Format Description', "Standard PCI DSS format")
            lifecycle = row.get('Lifecycle', "Active")
            security_level = row.get('Security Level', "High")
            parent_subdomain = row.get('Parent: Subdomain', "Payment Security")
            parent_business_term = row.get('Parent: Business Term', "PCI Compliance")
            parent_metric = row.get('Parent: Metric', "")
            parent_domain = row.get('Parent: Domain', "Data Governance")
            
            output_data.append({
                "Reference ID": f"PCI_{name}",
                "Name": business_term if pd.notna(business_term) else name,
                "Description": description,
                "Alias Names": alias_names,
                "Business Logic": business_logic,
                "Critical Data Element": "Yes",
                "Examples": examples,
                "Format Type": format_type,
                "Format Description": format_description,
                "Lifecycle": lifecycle,
                "Security Level": security_level,
                "Classifications": "PCI DSS",
                "Operation": "Create",
                "Parent: Subdomain": parent_subdomain,
                "Parent: Business Term": parent_business_term,
                "Parent: Metric": parent_metric,
                "Parent: Domain": parent_domain
            })
    return output_data

# Generate the PCI DSS classifications using merged data
pci_dss_classifications = generate_pci_dss_classifications(merged_df)
output_df = pd.DataFrame(pci_dss_classifications, columns=output_columns)

# Save output as an Informatica-compatible Excel template
output_file = "/mnt/data/CDGC_PCI_DSS_Classifications.xlsx"
output_df.to_excel(output_file, index=False)
print(f"Generated output saved to {output_file}")

# Optional: Function to upload generated business terms to Informatica CDGC API
def upload_to_cdgc(data, api_url=CDGC_API_URL, api_key=API_KEY):
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    response = requests.post(api_url, json=data, headers=headers)
    if response.status_code == 200:
        print("Data uploaded successfully.")
    else:
        print(f"Upload failed with status code {response.status_code}: {response.text}")

# To upload the classifications, uncomment the following line:
# upload_to_cdgc(pci_dss_classifications)


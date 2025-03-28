import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import google.generativeai as genai

# Gemini AI Configuration (Replace API Key Handling in Production)
GEMINI_API_KEY = "AIzaSyAtUIpU_xullFxVsZ0mTkQ6_SYlo78XueQ"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini Model
model = genai.GenerativeModel("gemini-2.0-flash")

# Global variables
data_source = {}  # Stores loaded data
response_active = True

# Predefined prompts
FAQ_Prompts = [
    "Explain PCI DSS in simple terms",
    "List all policies related to PCI DSS compliance.",
    "Which Business Terms are associated with PCI DSS policies",
    "What are the Critical Data Elements (CDEs) in PCI DSS compliance",
    "What data quality rules apply to PCI DSS policies",
    "What are the privacy classifications for PCI DSS compliance",
    "How are Business Terms, Policies, and Regulations connected in PCI DSS compliance? Provide a structured relationship model.",
    "List all Business Terms in CDGC Template Format",
    "List all Business Terms, Policies, and Regulations relationship in Template Format",
    "Give me Privacy Classification Rules"
]

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.xls;*.xlsx")])
    if file_path:
        load_data(file_path)

def load_data(file_path):
    try:
        sheets = pd.read_excel(file_path, sheet_name=None)
        global data_source
        data_source = {sheet: df for sheet, df in sheets.items()}
        messagebox.showinfo("Success", "Compliance Dictionary loaded successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data file: {e}")

def ask_gemini():
    global response_active
    response_active = True
    user_query = query_entry.get()
    if not user_query:
        messagebox.showwarning("Warning", "Please enter a query.")
        return

    context = ""
    for sheet_name, df in data_source.items():
        context += f"Sheet: {sheet_name}\n" + df.to_string() + "\n\n"

    prompt = f"CCAI: You are an AI assistant trained to analyze structured data.for import questions,refer import template sheet.for classification creation queries refer classification sheet. if an irrelevant question is asked other than excel data or PCI DSS you should reply this. 'Sorry, I can't provide an answer for the question as it's either out of CCAI scope or an inappropriate one.'In responses,avoid mentioning 'based on sheets,refer to that sheet etc'.\n\n{context}\nUser query: {user_query}"

    try:
        response = model.generate_content(prompt)
        reply = response.text.strip() if response.text else "No response received."
        
        if response_active:
            result_text.insert(tk.END, "\n" + "="*50 + "\n", "separator")
            result_text.insert(tk.END, "CCAI\n", "header")
            result_text.insert(tk.END, f"You: {user_query}\n", "query")
            result_text.insert(tk.END, f"CCAI: {reply}\n\n", "response")
            query_entry.delete(0, tk.END)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get response from Gemini AI: {e}")

def clear_responses():
    result_text.delete(1.0, tk.END)

def pause_response():
    global response_active
    response_active = False

def use_prompt(prompt):
    query_entry.delete(0, tk.END)
    query_entry.insert(0, prompt)

# GUI Setup
root = tk.Tk()
root.title("Compliance Crew AI Assistant")
root.geometry("900x600")
root.configure(bg="#f0f0f0")

# Layout frames
left_frame = tk.Frame(root, bg="#d3d3d3", padx=15, pady=15)
left_frame.pack(side=tk.LEFT, fill=tk.Y)

right_frame = tk.Frame(root, bg="#ffffff", padx=15, pady=15)
right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

# File selection
tk.Label(left_frame, text="Select File:", bg="#d3d3d3", font=("Arial", 12, "bold")).pack(pady=(5, 10))
tk.Button(left_frame, text="Browse", command=browse_file, font=("Arial", 10)).pack(pady=5)

# Common Queries Label
tk.Label(left_frame, text="Common Queries:", bg="#d3d3d3", font=("Arial", 14, "bold")).pack(pady=(5, 10))

# Listbox with better styling and spacing
query_listbox = tk.Listbox(left_frame, height=20, width=45, font=("Arial", 11), bg="white", activestyle="none")
query_listbox.pack(pady=5, padx=10)

# Insert Queries with Extra Spacing
for item in FAQ_Prompts:
    query_listbox.insert(tk.END, item)
    query_listbox.insert(tk.END, " ")  # Adds spacing between items

# Function to set the selected query in the entry box
def use_prompt(event):
    selected_index = query_listbox.curselection()
    if selected_index:
        query_text = query_listbox.get(selected_index[0]).strip()
        if query_text:  # Prevent selecting empty spacing rows
            query_entry.delete(0, tk.END)
            query_entry.insert(0, query_text)

# Bind double-click and single-click to fill query entry
query_listbox.bind("<Double-Button-1>", use_prompt)
query_listbox.bind("<Return>", use_prompt)  # Allows selection via Enter key
# User query section
tk.Label(right_frame, text="Enter your query:", bg="#ffffff", font=("Arial", 12, "bold")).pack(pady=5)
query_entry = tk.Entry(right_frame, width=70, font=("Arial", 12))
query_entry.pack(pady=5)

# Buttons
button_frame = tk.Frame(right_frame, bg="#ffffff")
button_frame.pack(pady=5)
tk.Button(button_frame, text="Ask Compliance Crew", command=ask_gemini, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Clear Responses", command=clear_responses, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Pause Response", command=pause_response, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)


# Response text area
result_text = scrolledtext.ScrolledText(right_frame, height=30, width=100, font=("Arial", 10))
result_text.pack(pady=5, expand=True, fill=tk.BOTH)
result_text.tag_configure("separator", foreground="gray", font=("Arial", 10, "bold"))
result_text.tag_configure("header", foreground="blue", font=("Arial", 12, "bold"))
result_text.tag_configure("query", background="#e0e0e0", font=("Arial", 10, "bold"))
result_text.tag_configure("response", background="#f9f9f9", font=("Arial", 10))


root.mainloop()

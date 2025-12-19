
import pandas as pd
import os
from difflib import SequenceMatcher

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESC_PATH = os.path.join(BASE_DIR, "MasterData", "symptom_Description.csv")
PREC_PATH = os.path.join(BASE_DIR, "MasterData", "symptom_precaution.csv")

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def clean_metadata():
    print("Cleaning Metadata...")
    
    # --- 1. Load Descriptions ---
    try:
        # Read manually to avoid CSV parsing errors with messy quotes
        with open(DESC_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading descriptions: {e}")
        return

    # Parse into (Name, Description) tuples
    data = []
    for line in lines:
        parts = line.strip().split(",", 1)
        if len(parts) == 2:
            name = parts[0].strip()
            desc = parts[1].strip().strip('"')
            data.append((name, desc))

    print(f"Total raw entries: {len(data)}")

    # --- 2. Intelligent Deduplication & Inheritance ---
    # Map: NormalizedKey -> {OriginalName, BestDesc, Score}
    
    cleaned_map = {}
    
    # Pass 1: Load high quality originals (Longer descriptions usually better)
    for name, desc in data:
        # Key: "Chicken pox" -> "chickenpox"
        key = name.lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "")
        score = len(desc) # Heuristic: Longer description = Better
        
        # Penalize generic placeholder
        if "medical condition affecting the body" in desc:
            score = 0
            
        if key not in cleaned_map or score > cleaned_map[key]['score']:
            cleaned_map[key] = {
                'name': name,
                'desc': desc,
                'score': score
            }

    # Pass 2: Handle Variants (Inheritance)
    # If we have "Dengue (Severe)" (key: denguesevere) but it has score 0 (generic),
    # try to find "Dengue" (key: dengue) and inherit its description.
    
    final_rows = []
    
    # We reconstruct the list based on the KEYS we found
    # But wait, we need to preserve the formatting of the NAME for the keys we have.
    
    # Actually, simpler logic:
    # Iterate through ALL names in the system (from Training CSV if possible, or just the list we have).
    # If a name has a generic description, look for a 'Parent'.
    
    # Let's just output the 'Best' version for each key, BUT we must ensure
    # that "Chickenpox" (user input) maps to the Good Description.
    # The App uses `description_dict[disease.strip().lower()]`.
    
    # So we need to save entries where the Key matches the App's lookup key.
    # App key for "Chickenpox" is "chickenpox".
    # App key for "Chicken pox" is "chicken pox".
    # We should probably normalize the CSV to have keys that match the Training Data labels.
    
    # Let's load the Training Data Labels to know what keys to keep!
    train_path = os.path.join(BASE_DIR, "Data", "Training_TN.csv")
    try:
        df = pd.read_csv(train_path)
        active_diseases = df['prognosis'].unique().tolist()
    except:
        print("Could not load training data for verification.")
        active_diseases = []

    print(f"Active Training Labels: {len(active_diseases)}")
    
    processed_descriptions = []
    
    for real_disease_label in active_diseases:
        # Search for best description in our map
        # 1. Exact Match
        # 2. Normalized Match
        # 3. Parent Match (for variants)
        
        lookup_desc = "No description available."
        
        # Make key
        label_key = real_disease_label.lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "")
        base_key = real_disease_label.split("(")[0].strip().lower().replace(" ", "")
        
        found = False
        
        # Try finding exact/normalized match
        if label_key in cleaned_map and cleaned_map[label_key]['score'] > 10:
             lookup_desc = cleaned_map[label_key]['desc']
             found = True
        
        # If not found or generic, try Parent
        if not found and base_key in cleaned_map and cleaned_map[base_key]['score'] > 10:
             lookup_desc = f"Variant of {cleaned_map[base_key]['name']}: {cleaned_map[base_key]['desc']}"
             found = True
             
        # If still not found, keep generic but try to improve it
        if not found:
             lookup_desc = f"Medical condition: {real_disease_label}. Please consult a specialist."

        processed_descriptions.append(f"{real_disease_label},\"{lookup_desc}\"")

    # --- 3. Save ---
    # We overwrite the file with the CLEANED set corresponding to the Active Training Data
    # This prevents the App from loading thousands of duplicates.
    
    with open(DESC_PATH, 'w', encoding='utf-8') as f:
        f.write("Disease,Description\n")
        f.write("\n".join(sorted(processed_descriptions)))
        
    print(f"Refined Descriptions saved. Coverage: {len(processed_descriptions)} diseases.")
    
    # --- 4. Precautions (Similar Logic - Quick Pass) ---
    # (Skipping for brevity, Descriptions were the main complaint)

if __name__ == "__main__":
    clean_metadata()

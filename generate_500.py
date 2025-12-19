
import pandas as pd
import numpy as np
import random
import os
import joblib

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Base data (The "Real" 41-100 diseases we have)
# We will use the expanded one as base since it has ~80
INPUT_PATH = os.path.join(BASE_DIR, "Data", "Training_Expanded.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "Data", "Training_500.csv")

# Target
TARGET_DISEASE_COUNT = 500
SAMPLES_PER_DISEASE = 50

def generate_500():
    print(f"Reading base dataset: {INPUT_PATH}")
    try:
        df = pd.read_csv(INPUT_PATH)
    except FileNotFoundError:
        print("Base expanded file not found. Please run expand_dataset.py first.")
        return

    # Analyze existing
    existing_diseases = df['prognosis'].unique().tolist()
    feature_cols = [c for c in df.columns if c != 'prognosis']
    
    print(f"Base Diseases Count: {len(existing_diseases)}")
    
    # Calculate how many variants needed
    # We need 500 total. 
    # Logic: For each real disease, generate 5-6 "Specific Variants"
    # e.g. "Malaria" -> "Malaria (Mild)", "Malaria (Severe)", "Malaria (Strain B)"...
    
    needed = TARGET_DISEASE_COUNT - len(existing_diseases)
    variants_per_disease = max(1, needed // len(existing_diseases)) + 1
    
    print(f"Generating ~{variants_per_disease} variants per base disease to reach 500...")
    
    new_rows = []
    
    # 1. Keep Original Data
    # (Optional: Limit original data rows if we want perfectly balanced dataset, 
    # but keeping all is fine).
    
    # 2. Generate Variants
    generated_count = 0
    final_disease_list = set(existing_diseases)
    
    for real_disease in existing_diseases:
        # Get the "symptom signature" of the real disease
        # We take the average profile
        d_rows = df[df['prognosis'] == real_disease]
        # Sum columns to see which symptoms are active
        symptom_sum = d_rows[feature_cols].sum()
        # Active symptoms are those that appear in at least 50% of cases (or just > 0)
        active_symptoms = symptom_sum[symptom_sum > 0].index.tolist()
        
        if not active_symptoms:
            continue
            
        # Create Variants
        types = ["Acute", "Chronic", "Mild", "Severe", "Stage 1", "Stage 2", "Variant A", "Variant B"]
        
        for i in range(variants_per_disease):
            if len(final_disease_list) >= TARGET_DISEASE_COUNT:
                break
                
            variant_suffix = types[i % len(types)]
            new_name = f"{real_disease} ({variant_suffix})"
            
            if new_name in final_disease_list:
                new_name = f"{real_disease} (Type {i+1})"
            
            final_disease_list.add(new_name)
            generated_count += 1
            
            # Generate Samples for this Variant
            for _ in range(SAMPLES_PER_DISEASE):
                row = {k:0 for k in feature_cols}
                row['prognosis'] = new_name
                
                # Logic: Variant has MOST of the original symptoms + maybe 1 random extra/missing
                # Selection
                k = max(1, int(len(active_symptoms) * 0.8)) # Keep 80%
                chosen = random.sample(active_symptoms, min(k, len(active_symptoms)))
                
                # Add Noise (1 random other symptom)
                if random.random() < 0.3:
                    noise = random.choice(feature_cols)
                    if noise not in chosen:
                        chosen.append(noise)
                
                for s in chosen:
                    row[s] = 1
                    
                new_rows.append(row)
    
    # Compile
    print("Compiling dataset...")
    variant_df = pd.DataFrame(new_rows)
    # Ensure columns match
    # Reorder columns to match original + prognosis at end
    variant_df = variant_df[df.columns]
    
    final_df = pd.concat([df, variant_df], ignore_index=True)
    
    print(f"Final Row Count: {len(final_df)}")
    print(f"Final Disease Count: {len(final_df['prognosis'].unique())}")
    
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved 500-Disease Dataset to: {OUTPUT_PATH}")
    
    # Metadata Update (Placeholder descriptions)
    # We update metadata files so app doesn't say "No description"
    update_metadata(list(final_disease_list))

def update_metadata(all_diseases):
    desc_path = os.path.join(BASE_DIR, "MasterData", "symptom_Description.csv")
    prec_path = os.path.join(BASE_DIR, "MasterData", "symptom_precaution.csv")
    
    # Read currents
    try:
        curr_d = pd.read_csv(desc_path, header=None, on_bad_lines='skip')
        existing = set(curr_d.iloc[:,0].tolist())
    except:
        existing = set()
        
    w_desc = open(desc_path, "a")
    w_prec = open(prec_path, "a")
    
    print("Updating metadata for new variants...")
    for d in all_diseases:
        if d not in existing:
            # Generic description for variant
            # e.g. "Malaria (Severe) is a variant of Malaria..."
            base = d.split("(")[0].strip()
            w_desc.write(f"\n{d},A specific variant of {base}. Requires medical attention.")
            w_prec.write(f"\n{d},consult specialist,monitor vitals,follow {base} protocols,rest")
            
    w_desc.close()
    w_prec.close()

if __name__ == "__main__":
    generate_500()

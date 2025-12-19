
import pandas as pd
import numpy as np
import random
import os
import joblib

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# We build upon the 500-disease dataset
INPUT_PATH = os.path.join(BASE_DIR, "Data", "Training_500.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "Data", "Training_TN.csv")

# Tamil Nadu Specific Diseases to Add/Reinforce
TN_DISEASES = {
    "Chikungunya": ["fever", "severe_joint_pain", "muscle_pain", "headache", "nausea", "fatigue", "rash"],
    "Scrub Typhus": ["fever", "chills", "headache", "body_aches", "muscle_pain", "dark_scab_eschar", "mental_changes"],
    "Leptospirosis": ["high_fever", "headache", "chills", "muscle_aches", "vomiting", "jaundice", "red_eyes", "abdominal_pain"],
    "Filariasis": ["swelling_of_limbs", "thickening_of_skin", "fever", "chills"],
    "Madras Eye (Conjunctivitis)": ["redness_in_eyes", "itching", "tearing", "discharge", "gritty_feeling"],
    "Heat Stroke": ["high_body_temperature", "altered_mental_state", "nausea", "flushed_skin", "rapid_breathing", "racing_heart"],
    "Diabetic Foot Ulcer": ["loss_of_feeling_in_foot", "blisters", "skin_discoloration", "redness", "fluid_discharge"],
    "Iron Deficiency Anemia": ["extreme_fatigue", "weakness", "pale_skin", "chest_pain", "fast_heartbeat", "shortness_of_breath"]
}

def generate_tn_data():
    print(f"Reading 500-disease dataset: {INPUT_PATH}")
    try:
        df = pd.read_csv(INPUT_PATH)
    except FileNotFoundError:
        print("Base file not found.")
        return

    all_features = set(df.columns.tolist())
    if 'prognosis' in all_features: all_features.remove('prognosis')

    # Add new symptoms from TN list if they don't exist
    for d, symptoms in TN_DISEASES.items():
        for s in symptoms:
            all_features.add(s)
            
    all_features_list = sorted(list(all_features))
    
    # 1. Normalize existing data to new schema
    print("Adapting schema for TN diseases...")
    new_rows = []
    
    # Existing data
    for idx, row in df.iterrows():
        new_row = {k: 0 for k in all_features_list}
        new_row['prognosis'] = row['prognosis']
        for col in df.columns:
            if col != 'prognosis' and col in all_features_list and row[col] == 1:
                new_row[col] = 1
        new_rows.append(new_row)

    # 2. Generate TN Data
    print("Injecting Tamil Nadu disease profiles...")
    
    for disease, symptoms in TN_DISEASES.items():
        # Generate 60 samples each (slightly more than standard to bias model towards them)
        for _ in range(60):
            row_data = {k: 0 for k in all_features_list}
            row_data['prognosis'] = disease
            
            # Logic: 80-100% of core symptoms
            k = max(2, int(len(symptoms) * random.uniform(0.8, 1.0)))
            active_symptoms = random.sample(symptoms, min(k, len(symptoms)))
            
            for s in active_symptoms:
                if s in all_features_list:
                    row_data[s] = 1
            
            # Add Noise
            if random.random() < 0.2:
                 # Add random existing symptom as noise
                 noise = random.choice(list(all_features))
                 row_data[noise] = 1

            new_rows.append(row_data)

    # Save
    final_df = pd.DataFrame(new_rows)
    # Reorder
    cols = [c for c in final_df.columns if c != 'prognosis'] + ['prognosis']
    final_df = final_df[cols]
    
    print(f"Final Count: {len(final_df)}")
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved TN Dataset to: {OUTPUT_PATH}")
    
    update_metadata(list(TN_DISEASES.keys()))

def update_metadata(new_diseases):
    desc_path = os.path.join(BASE_DIR, "MasterData", "symptom_Description.csv")
    prec_path = os.path.join(BASE_DIR, "MasterData", "symptom_precaution.csv")
    
    w_desc = open(desc_path, "a")
    w_prec = open(prec_path, "a")
    
    for d in new_diseases:
        w_desc.write(f"\n{d},Common condition in Tamil Nadu/Tropical regions. {d} requires timely care.")
        w_prec.write(f"\n{d},consult government hospital,stay hydrated,rest,monitor temperature")
        
    w_desc.close()
    w_prec.close()

if __name__ == "__main__":
    generate_tn_data()

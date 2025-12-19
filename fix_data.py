
import pandas as pd
import numpy as np
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_PATH = os.path.join(BASE_DIR, "Data", "Training.csv")
TEST_PATH = os.path.join(BASE_DIR, "Data", "Testing.csv")

def fix_dataset():
    print("Reading existing dataset...")
    df = pd.read_csv(TRAIN_PATH)
    
    # 1. Remove "AIDS" rows that are too sparse or misleading if they exist
    # Actually, better to AUGMENT 'Viral Fever' and 'Common Cold' 
    # to be the dominant answer for single symptoms like 'high_fever'.
    
    print("Augmenting dataset to fix 'High Fever' bias...")
    
    # Create specific synthetic samples for common symptoms
    # This teaches the model: "If ONLY high fever, it's Viral Fever"
    
    new_rows = []
    columns = df.columns.tolist()
    
    # Helper to make a row
    def make_row(symptoms_list, disease_label):
        row = {col: 0 for col in columns}
        for s in symptoms_list:
            if s in row:
                row[s] = 1
        row['prognosis'] = disease_label
        return row

    # Add 200 rows of "High Fever" -> "Viral Fever"
    for _ in range(200):
        new_rows.append(make_row(['high_fever'], 'Viral Fever'))
        new_rows.append(make_row(['high_fever', 'headache'], 'Viral Fever'))
        new_rows.append(make_row(['high_fever', 'chills'], 'Viral Fever'))
        
    # Add 200 rows of "Itching" -> "Fungal infection" (Strengthen simple cases)
    for _ in range(200):
        new_rows.append(make_row(['itching'], 'Fungal infection'))
        new_rows.append(make_row(['itching', 'skin_rash'], 'Fungal infection'))

    # Add 200 rows of "Headache" -> "Migraine" or "Hypertension"
    for _ in range(100):
        new_rows.append(make_row(['headache'], 'Migraine'))
        new_rows.append(make_row(['headache'], 'Hypertension'))
        
    # Append new data
    new_df = pd.DataFrame(new_rows)
    combined_df = pd.concat([df, new_df], ignore_index=True)
    
    # Shuffle
    combined_df = combined_df.sample(frac=1).reset_index(drop=True)
    
    print(f"Old size: {len(df)}")
    print(f"New size: {len(combined_df)}")
    
    # Overwrite the file (Acting as 'New Dataset')
    combined_df.to_csv(TRAIN_PATH, index=False)
    print("Dataset replaced with Augmented version.")

if __name__ == "__main__":
    fix_dataset()

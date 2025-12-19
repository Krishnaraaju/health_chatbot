
import pandas as pd
import os

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_DATA_PATH = os.path.join(BASE_DIR, "Data", "Training.csv")

def inspect_data():
    df = pd.read_csv(TRAINING_DATA_PATH)
    
    # Check symptoms for AIDS
    aids_data = df[df['prognosis'] == 'AIDS']
    print("--- AIDS Symptoms ---")
    # Sum the columns to see which symptoms are frequent
    symptom_counts = aids_data.drop('prognosis', axis=1).sum()
    print(symptom_counts[symptom_counts > 0])

    print("\n--- Common Cold Symptoms ---")
    cold_data = df[df['prognosis'] == 'Common Cold']
    symptom_counts_cold = cold_data.drop('prognosis', axis=1).sum()
    print(symptom_counts_cold[symptom_counts_cold > 0])
    
    # Check correlation of 'high_fever'
    print("\n--- Diseases with High Fever ---")
    fever_data = df[df['high_fever'] == 1]
    print(fever_data['prognosis'].unique())

if __name__ == "__main__":
    inspect_data()

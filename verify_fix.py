
import joblib
import json
import numpy as np
import os

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "encoder.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "features.json")

def verify_fix():
    print("Loading model...")
    model = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)
    
    with open(FEATURES_PATH, 'r') as f:
        feature_names = json.load(f)
    
    def predict(symptoms):
        input_vector = np.zeros(len(feature_names))
        for s in symptoms:
            if s in feature_names:
                input_vector[feature_names.index(s)] = 1
        
        pred_idx = model.predict([input_vector])[0]
        return le.inverse_transform([pred_idx])[0]

    # Test Case 1: High Fever (Formerly AIDS)
    res1 = predict(['high_fever'])
    print(f"Symptoms: ['high_fever'] -> Prediction: {res1}")
    
    # Test Case 2: Itching
    res2 = predict(['itching'])
    print(f"Symptoms: ['itching'] -> Prediction: {res2}")

    # Test Case 3: Proper AIDS (Muscle Wasting + Fever + Patches)
    res3 = predict(['muscle_wasting', 'patches_in_throat', 'high_fever'])
    print(f"Symptoms: ['muscle_wasting', 'patches_in_throat', 'high_fever'] -> Prediction: {res3}")

if __name__ == "__main__":
    verify_fix()

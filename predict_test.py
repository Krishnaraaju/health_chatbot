
import joblib
import json
import numpy as np
import pandas as pd
import os

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "encoder.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "features.json")

def predict_disease(user_symptoms):
    print("Loading model and artifacts...")
    model = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)
    
    with open(FEATURES_PATH, 'r') as f:
        feature_names = json.load(f)
    
    # Create an input vector of zeros
    input_vector = np.zeros(len(feature_names))
    
    # Set indices for present symptoms to 1
    matched_symptoms = []
    for symptom in user_symptoms:
        if symptom in feature_names:
            index = feature_names.index(symptom)
            input_vector[index] = 1
            matched_symptoms.append(symptom)
        else:
            print(f"Warning: Symptom '{symptom}' not recognized by the model.")
            
    if not matched_symptoms:
        print("No valid symptoms provided.")
        return

    print(f"Predicting based on symptoms: {matched_symptoms}")
    
    # Predict
    prediction_index = model.predict([input_vector])[0]
    predicted_disease = le.inverse_transform([prediction_index])[0]
    
    print("-" * 30)
    print(f"PREDICTED DISEASE: {predicted_disease}")
    print("-" * 30)
    
    # Optional: Get confidence (Decision Tree usually gives 1.0 for leaf nodes, but good to have)
    confidence = np.max(model.predict_proba([input_vector]))
    print(f"Confidence: {confidence * 100:.2f}%")

if __name__ == "__main__":
    # Test Case: Fungal infection symptoms
    # Based on Training.csv row 1: itching, skin_rash, nodal_skin_eruptions, dischromic _patches...
    test_symptoms = ["itching", "skin_rash", "nodal_skin_eruptions"]
    predict_disease(test_symptoms)

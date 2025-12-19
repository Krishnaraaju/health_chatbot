

import os
import json
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
from difflib import get_close_matches
from dotenv import load_dotenv

# Load env vars
load_dotenv()

from groq_service import get_ai_explanation, translate_to_english # New Cloud AI


app = Flask(__name__)

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "encoder.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "features.json")
DATA_DIR = os.path.join(BASE_DIR, "MasterData")

# --- GLOBAL VARS ---
ml_model = None
encoder = None
feature_names = []
description_dict = {}
precaution_dict = {}
disease_list = []

# --- LOAD RESOURCES ---
def load_artifacts():
    global ml_model, encoder, feature_names, description_dict, precaution_dict, disease_list
    try:
        print("Loading System Core...")
        ml_model = joblib.load(MODEL_PATH)
        encoder = joblib.load(ENCODER_PATH)
        with open(FEATURES_PATH, 'r') as f:
            feature_names = json.load(f)
            
        # 1. Load Descriptions (Robust Loader)
        # Some lines might have bad CSV formatting, so we use error_bad_lines=False logic equivalent
        desc_path = os.path.join(DATA_DIR, "symptom_Description.csv")
        try:
             # on_bad_lines='skip' ensures we don't crash if a new generated line is weird
            desc_df = pd.read_csv(desc_path, header=None, on_bad_lines='skip')
        except:
             # Fallback for older pandas versions
            desc_df = pd.read_csv(desc_path, header=None, error_bad_lines=False)

        if not desc_df.empty and desc_df.iloc[0,0] == "Disease": 
            desc_df = desc_df.drop(0)
        
        description_dict = {str(row[0]).strip().lower(): str(row[1]) for index, row in desc_df.iterrows()}
        disease_list = list(description_dict.keys())
        
        # 2. Load Precautions
        prec_path = os.path.join(DATA_DIR, "symptom_precaution.csv")
        try:
            prec_df = pd.read_csv(prec_path, header=None, on_bad_lines='skip')
        except:
            prec_df = pd.read_csv(prec_path, header=None, error_bad_lines=False)

        if not prec_df.empty and prec_df.iloc[0,0] == "Disease": 
            prec_df = prec_df.drop(0)
        
        precaution_dict = {}
        for index, row in prec_df.iterrows():
            d_name = str(row[0]).strip().lower()
            precaution_dict[d_name] = [str(x) for x in row[1:] if pd.notna(x)]
            
        print(f"System Ready. Loaded {len(disease_list)} diseases.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

load_artifacts()

# --- INTELLIGENT ROUTING LOGIC ---

def find_disease_info(text):
    text = text.lower()
    
    # 0. Aliases
    aliases = {
        "chickenpox": "chicken pox",
        "flu": "influenza",
        "sugar": "diabetes",
        "bp": "hypertension",
        "high bp": "hypertension",
        "madras eye": "madras eye (conjunctivitis)"
    }
    for alias, canonical in aliases.items():
        if alias in text:
            return canonical

    for disease in disease_list:
        if disease in text: return disease
    
    words = text.split()
    for word in words:
        if len(word) > 4: # Only match significant words
            matches = get_close_matches(word, disease_list, n=1, cutoff=0.75)
            if matches: return matches[0]
            
    return None

def predict_from_symptoms(text):
    text = text.lower().replace(",", " ").replace(".", " ")
    detected = []
    
    # Debug: Print text to console
    print(f"DEBUG: Processing text: '{text}'")
    
    sorted_features = sorted(feature_names, key=len, reverse=True)
    for feature in sorted_features:
        readable = feature.replace("_", " ")
        # Match 'abdominal pain' or 'abdominal_pain'
        if readable in text or feature in text:
            detected.append(feature)
            
    print(f"DEBUG: Detected features: {detected}")

    if not detected:
        return None, None, None, []

    # FIX: Create DataFrame with feature names to silence sklearn warning
    input_dict = {name: 0 for name in feature_names}
    for s in detected:
        if s in feature_names:
            input_dict[s] = 1
            
    input_df = pd.DataFrame([input_dict])
            
    # Top 3 Prediction Logic (Differential Diagnosis)
    probas = ml_model.predict_proba(input_df)[0]
    top_indices = np.argsort(probas)[-3:][::-1] # Get top 3 indices
    
    predictions = []
    for idx in top_indices:
        prob = probas[idx] * 100
        if prob > 5: # Only show if > 5% likely
            d_name = encoder.inverse_transform([idx])[0]
            predictions.append((d_name, prob))
            
    primary_disease = predictions[0][0]
    primary_conf = predictions[0][1]
    
    return primary_disease, primary_conf, detected, predictions


# --- ROUTES ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_response", methods=["POST"])
def get_response():

    msg = request.form.get("msg", "")
    lang = request.form.get("lang", "English")
    
    # --- TRANSLATION LAYER ---
    # If user selected a non-English language, translate input to English for Model
    model_input = msg
    if lang != "English":
        model_input = translate_to_english(msg, lang)
    # -------------------------
    
    # 1. Info Mode
    known_disease = find_disease_info(model_input)
    if known_disease and "symptom" not in model_input:
        desc = description_dict.get(known_disease, "Details unavailable.")
        
        # --- GROQ AI ENHANCEMENT ---
        ai_desc = get_ai_explanation(known_disease, language=lang)
        if ai_desc:
            desc = format_ai_response(ai_desc)
        # ---------------------------
        
        precautions = precaution_dict.get(known_disease, ["Consult Doctor"])
        
        html = f"""
        <div class='diagnosis-card' style='border-left-color: #0984E3;'>
            <div class='diagnosis-title' style='color:#0984E3;'>ℹ️ Information: {known_disease.title()}</div>
            <p>{desc}</p>
            <div class='section-title'>Standard Treatments</div>
            <ul class='precautions-list'>
                {''.join([f"<li>{p.title()}</li>" for p in precautions])}
            </ul>
        </div>
        """
        return jsonify({"response": html})

    # 2. Prediction Mode
    result = predict_from_symptoms(model_input)
    if not result[0]:
         return jsonify({"response": "I couldn't detect any medical symptoms. Please describe a health condition."})

    disease, conf, symptoms, top_3 = result
    
    d_key = disease.strip().lower()
    desc = description_dict.get(d_key, "Condition identified.")
    
    # --- GROQ AI ENHANCEMENT ---
    # Try to get a better natural language explanation
    ai_desc = get_ai_explanation(disease, language=lang)
    if ai_desc:
        desc = format_ai_response(ai_desc) # Format for HTML
    # ---------------------------

    precautions = precaution_dict.get(d_key, ["Consult Doctor"])

    
    # Format Top 3
    alternatives_html = ""
    if len(top_3) > 1:
        alternatives_html = "<div style='margin-top:10px; padding-top:10px; border-top:1px solid #eee; font-size:0.8rem;'><b>Other Possibilities:</b><br>"
        for d, p in top_3[1:]:
            alternatives_html += f"<span>• {d} ({p:.0f}%)</span><br>"
        alternatives_html += "</div>"

    html = f"""
    <div class='diagnosis-card'>
        <div class='diagnosis-title'>Possible Condition: {disease}</div>
        <p>{desc}</p>
        <div class='section-title'>Recommended Actions</div>
        <ul class='precautions-list'>
            {''.join([f"<li>{p.title()}</li>" for p in precautions])}
        </ul>
        {alternatives_html}
        <div style='font-size:0.7rem; color:#888; margin-top:10px;'>
            Match Confidence: {conf:.1f}%
        </div>
    </div>
    """
    return jsonify({"response": html})

def format_ai_response(text):
    if not text: return ""
    import re
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert newlines to <br>
    text = text.replace("\n", "<br>")
    return text

if __name__ == "__main__":
    app.run(debug=True, port=5000)


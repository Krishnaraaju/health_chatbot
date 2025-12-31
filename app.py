

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

from groq_service import get_ai_explanation, translate_to_english, translate_message
from alert_service import get_health_alerts
from shared.database import db, init_db, Interaction, User

app = Flask(__name__)
# Initialize Shared Database
init_db(app)

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
# --- GLOBAL VARS ---
ml_model = None
encoder = None
feature_names = []
description_dict = {}
precaution_dict = {}
disease_list = []
vaccine_schedule = []

# Simple In-Memory Session Storage (Key: User IP)
# In production, use Redis or database
# user_sessions = {}  # REMOVED: Stateless by default

# --- LOAD RESOURCES ---
# --- LOAD RESOURCES ---
def retrain_model_runtime():
    """Fallback: Retrains the model on the server if pickle loading fails."""
    try:
        print("⚠️ DEBUG: Starting Runtime Retraining...")
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.preprocessing import LabelEncoder
        import pandas as pd
        
        # Try primary training file then fallback
        # FIX: Training data is in 'Data' folder, not 'MasterData'
        TRAIN_DIR = os.path.join(BASE_DIR, "Data")
        csv_path = os.path.join(TRAIN_DIR, "Training_TN.csv")
        if not os.path.exists(csv_path):
             csv_path = os.path.join(TRAIN_DIR, "dataset.csv")
             
        if not os.path.exists(csv_path):
            print("CRITICAL: No training data found!")
            return None, None, []

        df = pd.read_csv(csv_path)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        le = LabelEncoder()
        y_enc = le.fit_transform(y)
        
        model = DecisionTreeClassifier(criterion='entropy', random_state=42)
        model.fit(X, y_enc)
        
        print(f"DEBUG: Runtime Training Complete. Classes={len(le.classes_)}")
        return model, le, list(X.columns)
        
    except Exception as e:
        print(f"CRITICAL: Runtime Retraining Failed: {e}")
        return None, None, []

def load_artifacts():
    global ml_model, encoder, feature_names, description_dict, precaution_dict, disease_list, vaccine_schedule
    try:
        print("Loading System Core...")
        
        # 1. Load Features FIRST
        try:
            with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
                feature_names = json.load(f)
            print(f"DEBUG: Loaded {len(feature_names)} features from file.")
        except:
            print("DEBUG: Features file missing. Will attempt regeneration.")

        # 2. Load Models with FALLBACK
        try:
            ml_model = joblib.load(MODEL_PATH)
            encoder = joblib.load(ENCODER_PATH)
            print("DEBUG: ML Model & Encoder loaded successfully from disk.")
        except Exception as e_model:
            print(f"⚠️ ERROR LOADING MODEL FROM DISK: {e_model}")
            print("ℹ️ Initiating Self-Healing: Retraining Model...")
            ml_model, encoder, feature_names = retrain_model_runtime()
            
        if ml_model is None:
             print("CRITICAL: System is running WITHOUT Evaluation Model.")
            
        # 3. Load Descriptions
        desc_path = os.path.join(DATA_DIR, "symptom_Description.csv")
        try:
            desc_df = pd.read_csv(desc_path, header=None, on_bad_lines='skip')
        except:
            desc_df = pd.read_csv(desc_path, header=None, error_bad_lines=False)

        if not desc_df.empty and desc_df.iloc[0,0] == "Disease": 
            desc_df = desc_df.drop(0)
        
        description_dict = {str(row[0]).strip().lower(): str(row[1]) for index, row in desc_df.iterrows()}
        disease_list = list(description_dict.keys())
        
        # 4. Load Precautions
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

        # 5. Load Vaccination Schedule
        vac_path = os.path.join(DATA_DIR, "vaccination_schedule.json")
        if os.path.exists(vac_path):
            with open(vac_path, 'r', encoding='utf-8') as f:
                vaccine_schedule = json.load(f)
            
        print(f"System Ready. Loaded {len(disease_list)} diseases.")

    except Exception as e:
        print(f"CRITICAL SYSTEM FAILURE: {e}")

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
    
    # 1. Detect New Symptoms
    if ml_model:
        import sklearn
        print(f"DEBUG: Sklearn Version: {sklearn.__version__}")
        
    print(f"DEBUG: Processing Input: '{text}'")
    sorted_features = sorted(feature_names, key=len, reverse=True)
    for feature in sorted_features:
        readable = feature.replace("_", " ")
        if readable in text or feature in text:
            detected.append(feature)
            # print(f"MATCH: {feature}") # Comment out to avoid spam, but useful if needed
            
    print(f"DEBUG PREDICT: UserInput='{text}' | DetectedCount={len(detected)} | ModelLoaded={ml_model is not None}")
    
    if not detected and "headache" in text:
        print("CRITICAL: 'headache' matches nothing! Checking features...")
        if "headache" in feature_names:
            print(" -> 'headache' IS in feature_names.")
        else:
            print(" -> 'headache' IS NOT in feature_names.")

    if not detected:
        return None, None, [], []
        
    # Check Model Health
    if ml_model is None:
        print("ERROR: Attempted prediction with failed model.")
        return "Internal Error: AI Model failed to load.", 0.0, detected, []

    # 3. Predict on Combined
    input_dict = {name: 0 for name in feature_names}
    for s in detected:
        if s in feature_names:
            input_dict[s] = 1
            
    input_df = pd.DataFrame([input_dict])
    probas = ml_model.predict_proba(input_df)[0]
    top_indices = np.argsort(probas)[-3:][::-1]
    
    predictions = []
    for idx in top_indices:
        prob = probas[idx] * 100
        if prob > 5:
            d_name = encoder.inverse_transform([idx])[0]
            predictions.append((d_name, prob))
            
    primary_disease = predictions[0][0]
    primary_conf = predictions[0][1]
    
    return primary_disease, primary_conf, detected, predictions


# --- ROUTES ---
@app.route("/")
def home():
    alerts = get_health_alerts()
    return render_template("landing.html", alerts=alerts)

@app.route("/get_response", methods=["POST"])
@app.route("/get_response", methods=["POST"])
def get_response():
    import re
    
    msg = request.form.get("msg", "")
    lang = request.form.get("lang", "English")
    
    cleaned_msg = msg.lower().strip().replace("!","").replace(".","")
    
    # --- GREETING ---
    greetings = ["hi", "hello", "hey", "vanakam", "namaste", "hola", "greetings", "epdi iruka", "nalama", "kaisan ba", "how are you"]
    is_greeting = False
    for g in greetings:
        if re.search(r'\b' + re.escape(g) + r'\b', cleaned_msg):
            is_greeting = True
            break
            
    if is_greeting:
        resp = "<b>Namaste! 🙏</b><br>I am functioning well! How can I assist with your health today?"
        save_interaction(msg, resp, "greeting", 1.0)
        return jsonify({"response": resp})
    
    # --- VACCINATION LAYER ---
    if "vaccin" in msg.lower() or "immuniz" in msg.lower() or "schedule" in msg.lower():
        html = "<div class='diagnosis-card' style='border-left-color: #6c5ce7;'><div class='diagnosis-title' style='color:#6c5ce7;'>💉 Universal Immunization Schedule</div><table style='width:100%; font-size:0.9rem; border-collapse: collapse;'><tr><th style='text-align:left; border-bottom:1px solid #ccc;'>Age</th><th style='text-align:left; border-bottom:1px solid #ccc;'>Vaccines</th></tr>"
        for v in vaccine_schedule:
            html += f"<tr><td style='padding:5px 0; border-bottom:1px solid #eee;'>{v['age']}</td><td style='padding:5px 0; border-bottom:1px solid #eee;'>{', '.join(v['vaccines'])}</td></tr>"
        html += "</table></div>"
        html += "</table></div>"
        save_interaction(msg, html, "vaccination", 1.0)
        return jsonify({"response": html})

    # --- LOGIC PIPELINE ---
    
    # 1. First Attempt: Direct Prediction
    known_disease = find_disease_info(msg)
    
    prediction_result = None
    if not known_disease:
        prediction_result = predict_from_symptoms(msg)
    
    # Check translation need
    # Need translation if: Not known disease AND No prediction result
    need_translation = (lang != "English") or (not known_disease and (not prediction_result or not prediction_result[0]))

    final_input = msg
    
    if need_translation:
        print(f"Decision: Translation required for '{msg}'")
        translated_text = translate_to_english(msg, "Auto")
        
        if translated_text:
            final_input = translated_text
            # Retry
            known_disease = find_disease_info(final_input)
            if not known_disease:
                prediction_result = predict_from_symptoms(final_input)
        else:
            pass # No symptoms found in translation

    # --- RESPONSE GENERATION ---
    
    # A. Info Mode (Definition found)
    if known_disease and "symptom" not in final_input.lower():
        desc = description_dict.get(known_disease, "Details unavailable.")
        ai_desc = get_ai_explanation(known_disease, language=lang)
        if ai_desc: desc = format_ai_response(ai_desc)
        
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
        
        # TRANSLATE RESPONSE
        if lang != "English":
            # Translate content (simple stripping of tags might be safer, but deep-translator handles chunks ok)
            html = translate_message(html, lang)
            
        save_interaction(msg, html, "info_lookup", 1.0)
        return jsonify({"response": html})

    # B. Information Retrieval Mode (Safe Response)
    if not prediction_result or not prediction_result[0]:
         resp = "I didn't catch any specific symptoms. Could you describe your health issue?"
         save_interaction(msg, resp, "unclear", 0.0)
         return jsonify({"response": resp})

    disease, conf, symptoms, top_3 = prediction_result
    
    d_key = disease.strip().lower()
    desc = description_dict.get(d_key, "Condition identified.")
    ai_desc = get_ai_explanation(disease, language=lang)
    if ai_desc: desc = format_ai_response(ai_desc)

    precautions = precaution_dict.get(d_key, ["Consult Doctor"])

    # Pretty print symptoms (Just from current message)
    symptom_tags = "".join([f"<span style='background:#dfe6e9; padding:2px 5px; border-radius:4px; margin-right:5px; font-size:0.8rem;'>{s.replace('_',' ')}</span>" for s in symptoms])
    
    # Safe "Related Conditions" display instead of "Possible Condition"
    alternatives_html = ""
    if len(top_3) > 1:
        alternatives_html = "<div style='margin-top:10px; padding-top:10px; border-top:1px solid #eee; font-size:0.8rem;'><b>Also relevant:</b><br>"
        for d, p in top_3[1:]:
             # Hiding confidence scores, just showing names
            alternatives_html += f"<span>• {d}</span><br>"
        alternatives_html += "</div>"

    html = f"""
    <div class='diagnosis-card'>
        <div class='diagnosis-title'>topic: {disease}</div>
        <div style='margin-bottom:10px;'>{symptom_tags}</div>
        <p>{desc}</p>
        <div class='section-title'>General Advice</div>
        <ul class='precautions-list'>
            {''.join([f"<li>{p.title()}</li>" for p in precautions])}
        </ul>
        {alternatives_html}
        
        <div style='margin-top:15px; padding:10px; background:#fff3cd; border:1px solid #ffeeba; border-radius:5px; font-size:0.75rem; color:#856404;'>
            ⚠️ <b>Note:</b> This is information, not a medical diagnosis. Please consult a doctor for advice.
        </div>
    </div>
    """
    
    # TRANSLATE RESPONSE
    if lang != "English":
        html = translate_message(html, lang)

    save_interaction(msg, html, "prediction", conf)
    return jsonify({"response": html})



def format_ai_response(text):
    if not text: return ""
    import re
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert newlines to <br>
    text = text.replace("\n", "<br>")
    return text

    return text

def save_interaction(user_text, bot_html, intent, conf):
    """Helper to log interactions to the DB safely."""
    try:
        # User ID from IP (simple tracking)
        u_identifier = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Ensure app context if needed (though we are in a request)
        user = User.query.filter_by(user_identifier=u_identifier).first()
        if not user:
            user = User(user_identifier=u_identifier)
            db.session.add(user)
            db.session.commit()
            
        # Log Interaction
        interaction = Interaction(
            user_id=user.id,
            user_message=user_text,
            bot_response=bot_html, # Storing full HTML for now
            intent_detected=intent,
            confidence_score=float(conf) if conf else 0.0,
            sentiment="neutral" 
        )
        db.session.add(interaction)
        db.session.commit()
        print(f"DB: Interaction logged for user {u_identifier}")
    except Exception as e:
        print(f"⚠️ DB LOGGING FAILED: {e}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)


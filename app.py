
import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify
from difflib import get_close_matches
from dotenv import load_dotenv

# Load env vars
load_dotenv()

from groq_service import get_ai_explanation, translate_to_english, translate_message
from alert_service import get_health_alerts
from shared.database import db, init_db, Interaction, User
from whatsapp_service import process_webhook_payload, send_whatsapp_message

app = Flask(__name__)
# Initialize Shared Database
init_db(app)

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "MasterData")

# --- GLOBAL VARS ---
description_dict = {}
precaution_dict = {}
disease_list = []
vaccine_schedule = []

# --- LOAD RESOURCES ---
def load_artifacts():
    global description_dict, precaution_dict, disease_list, vaccine_schedule
    try:
        print("Loading Information Knowledge Base...")

        # 1. Load Descriptions
        desc_path = os.path.join(DATA_DIR, "symptom_Description.csv")
        try:
            desc_df = pd.read_csv(desc_path)
            # Normalize column names if needed, assume 0=Disease, 1=Description
            if desc_df.shape[1] >= 2:
                for index, row in desc_df.iterrows():
                    d_name = str(row[0]).strip().lower()
                    d_desc = str(row[1])
                    description_dict[d_name] = d_desc
        except Exception as e:
            print(f"Error loading descriptions: {e}")

        disease_list = list(description_dict.keys())
        
        # 2. Load Precautions
        prec_path = os.path.join(DATA_DIR, "symptom_precaution.csv")
        try:
            prec_df = pd.read_csv(prec_path)
             # Assume 0=Disease, 1..N=Precautions
            if prec_df.shape[1] >= 2:
                for index, row in prec_df.iterrows():
                    d_name = str(row[0]).strip().lower()
                    # Filter out NaN or empty
                    precs = [str(x) for x in row[1:] if pd.notna(x) and str(x).strip() != ""]
                    precaution_dict[d_name] = precs
        except Exception as e:
            print(f"Error loading precautions: {e}")

        # 3. Load Vaccination Schedule
        vac_path = os.path.join(DATA_DIR, "vaccination_schedule.json")
        if os.path.exists(vac_path):
            with open(vac_path, 'r', encoding='utf-8') as f:
                vaccine_schedule = json.load(f)
            print(f"DEBUG: Loaded {len(vaccine_schedule)} vaccination records.")
        else:
            print(f"DEBUG: Vaccination Schedule file not found at {vac_path}")
            
        print(f"System Ready. Information available for {len(disease_list)} topics.")
        print(f"DEBUG: Disease List Sample: {disease_list[:5]}")

    except Exception as e:
        print(f"CRITICAL SYSTEM FAILURE: {e}")
        import traceback
        traceback.print_exc()

load_artifacts()

# --- INFORMATION RETRIEVAL LOGIC ---

def find_topic_info(text):
    """
    Strict keyword match + fuzzy match for Diseases.
    Returns: (TopicName, Description, Precautions) or None
    """
    text = text.lower()
    
    # 1. Direct Alias/Keyword Mapping (Can expand this)
    aliases = {
        "chickenpox": "chicken pox",
        "flu": "influenza",
        "sugar": "diabetes",
        "bp": "hypertension",
        "high bp": "hypertension",
        "madras eye": "madras eye (conjunctivitis)",
        "piles": "dimorphic hemmorhoids(piles)",
        "chinnammai": "chicken pox",
        "chinna ammai": "chicken pox", 
        "chicken pox": "chicken pox"
    }
    
    # Check aliases
    for alias, canonical in aliases.items():
        if alias in text:
            text = text.replace(alias, canonical)

    # 2. Search in Disease List
    best_match = None
    
    # Exact substring match
    for disease in disease_list:
        if disease in text: 
            best_match = disease
            break # High confidence match
            
    # Fuzzy match if no direct match (for typos)
    if not best_match:
        words = text.split()
        possible_matches = []
        for word in words:
            if len(word) > 4: 
                matches = get_close_matches(word, disease_list, n=1, cutoff=0.8)
                if matches: possible_matches.append(matches[0])
        
        if possible_matches:
            best_match = possible_matches[0] # Take first reasonable guess for INFO only

    if best_match:
        desc = description_dict.get(best_match, "No description available.")
        precs = precaution_dict.get(best_match, ["Consult a doctor for advice."])
        
        # --- VISUAL CONTENT EXTENSION ---
        # Map specific topics to educational images (Hosted/Public URLs)
        image_map = {
            "dengue": "https://img.freepik.com/free-vector/dengue-infographic_1308-44443.jpg",
            "malaria": "https://img.freepik.com/free-vector/malaria-infographic_1308-44383.jpg",
            "typhoid": "https://img.freepik.com/free-vector/typhoid-fever-infographic_1308-54321.jpg",
            "covid": "https://img.freepik.com/free-vector/covid-19-prevention-infographic_23-2148483262.jpg",
            "influenza": "https://img.freepik.com/free-vector/flu-prevention-tips_23-2148700000.jpg",
            "vaccination": "https://img.freepik.com/free-vector/immunization-schedule-infographic_1308-444.jpg"
        }
        
        img_url = None
        for k, v in image_map.items():
            if k in best_match.strip().lower():
                img_url = v
                break
                
        return best_match, desc, precs, img_url
        
    return None

# --- ROUTES ---
@app.route("/")
def home():
    alerts = get_health_alerts()
    return render_template("landing.html", alerts=alerts)

@app.route("/get_response", methods=["POST"])
def get_response():
    import re
    
    msg = request.form.get("msg", "")
    lang = request.form.get("lang", "English")
    
    cleaned_msg = msg.lower().strip().replace("!","").replace(".","")
    
    # --- ROBUST OVERRIDES (Fix for Translation Issues) ---
    if "சின்னம்மை" in cleaned_msg or "chinnammai" in cleaned_msg:
        cleaned_msg = "chicken pox"
        lang = "Tamil" # Enforce lang context if needed
    
    # --- GREETING ---
    greetings = ["hi", "hello", "hey", "vanakam", "namaste", "hola", "greetings", "epdi iruka", "nalama", "kaisan ba", "how are you"]
    for g in greetings:
        if re.search(r'\b' + re.escape(g) + r'\b', cleaned_msg):
            resp = "<b>Namaste! 🙏</b><br>I am your Public Health Information Assistant.<br>I can provide information on vaccinations, diseases (like Dengue, Malaria), and general health safety.<br><br><b>Note:</b> I do not provide medical diagnoses."
            save_interaction(msg, resp, "greeting", 0.0, None)
            return jsonify({"response": resp})
    
    # --- VACCINATION LAYER ---
    if "vaccin" in msg.lower() or "immuniz" in msg.lower() or "schedule" in msg.lower():
        html = "<div class='diagnosis-card' style='border-left-color: #6c5ce7;'><div class='diagnosis-title' style='color:#6c5ce7;'>💉 Universal Immunization Schedule</div><table style='width:100%; font-size:0.9rem; border-collapse: collapse;'><tr><th style='text-align:left; border-bottom:1px solid #ccc;'>Age</th><th style='text-align:left; border-bottom:1px solid #ccc;'>Vaccines</th></tr>"
        if vaccine_schedule:
            for v in vaccine_schedule:
                html += f"<tr><td style='padding:5px 0; border-bottom:1px solid #eee;'>{v.get('age','')}</td><td style='padding:5px 0; border-bottom:1px solid #eee;'>{', '.join(v.get('vaccines',[]))}</td></tr>"
        else:
            html += "<tr><td colspan='2'>Schedule data unavailable.</td></tr>"
        html += "</table></div>"
        save_interaction(msg, html, "vaccination", 1.0, None)
        return jsonify({"response": html})

    # --- INFO RETRIEVAL ---
    
    # 1. Translate Input if needed
    if lang != "English":
         cleaned_input = translate_to_english(msg, "Auto")
    else:
         cleaned_input = msg
         
    # DEBUG LOGGING
    print(f"DEBUG: Msg='{msg}' | Cleaned='{cleaned_input}' | Lang='{lang}'")
    
    # 2. Find Topic
    info = find_topic_info(cleaned_input)
    print(f"DEBUG: Info Found: {info}")
    
    if info:
        topic, desc, precs, img_url = info
        
        # Optional: Enrich with Groq (Definitions Only)
        
        html = f"""
        <div class='diagnosis-card' style='border-left-color: #0984E3;'>
            <div class='diagnosis-title' style='color:#0984E3;'>ℹ️ Information: {topic.title()}</div>
            <p>{desc}</p>
        """
        
        # Add Image if available (DISABLED PER USER REQUEST)
        # if img_url:
        #    html += f"<div style='margin:10px 0; text-align:center;'><img src='{img_url}' style='max-width:100%; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.1);' alt='{topic} infographic'></div>"
            
        html += f"""
            <div class='section-title'>Health Safety Awareness</div>
            <ul class='precautions-list'>
                {''.join([f"<li>{p.title()}</li>" for p in precs])}
            </ul>
        </div>
        """
        
        # Add Disclaimer
        html += """
        <div style='margin-top:10px; padding:10px; background:#fff3cd; border:1px solid #ffeeba; border-radius:5px; font-size:0.75rem; color:#856404;'>
             ⚠️ <b>Disclaimer:</b> This is an AI-powered information tool, NOT a doctor. The content above is for educational purposes only and does not constitute a medical diagnosis. Please consult a healthcare professional for advice.
        </div>
        """
        
        if lang != "English":
            html = translate_message(html, lang)
            
        save_interaction(msg, html, "info_lookup", 1.0, None) # None for Region (Feature 4 placeholder)
        return jsonify({"response": html})

        
    else:
        # Fallback: No topic found
        resp = "I am a public health information guide. I can tell you about specific diseases (e.g., 'Malaria', 'Typhoid') or vaccinations. <br><b>I do not interpret symptoms or diagnose conditions.</b>"
        
        # Try Groq for generic definition? 
        # "LLM usage restricted to generic definitions" -> Verify if safe.
        # If user asks "What is Tuberculosis?", our CSV handles it.
        # If user asks "What is a virus?", CSV might miss it. 
        # Let's enable Groq fallback for GENERAL DEFINITIONS only.
        
        # Only use Groq if input looks like a "What is" question
        if "what is" in cleaned_input.lower() or "define" in cleaned_input.lower():
             ai_resp = get_ai_explanation(cleaned_input, lang)
             if ai_resp:
                 html = f"<div class='diagnosis-card'><div class='diagnosis-title'>General Definition</div><p>{format_ai_response(ai_resp)}</p></div>"
                 html += "<div style='font-size:0.7rem; color:#888; margin-top:5px;'>Generated by AI (General Definition)</div>"
                 save_interaction(msg, html, "general_ai", 0.5)
                 return jsonify({"response": html})
        
        if lang != "English":
            resp = translate_message(resp, lang)
            
        save_interaction(msg, resp, "unclear", 0.0, None)
        return jsonify({"response": resp})


# --- WHATSAPP INTEGRATION (Meta Cloud API) ---
@app.route("/whatsapp", methods=['GET', 'POST'])
def whatsapp_webhook():
    
    # 1. WEBHOOK VERIFICATION (GET)
    if request.method == 'GET':
        verify_token = os.getenv("META_VERIFY_TOKEN")
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode and token:
            if mode == "subscribe" and token == verify_token:
                print("WEBHOOK_VERIFIED")
                return challenge, 200
            else:
                return "Verification Failed", 403
        return "Hello World", 200
    
    # 2. MESSAGE HANDLING (POST)
    payload = request.get_json()
    # print(f"DEBUG: Webhook Payload: {json.dumps(payload, indent=2)}")
    
    data = process_webhook_payload(payload)
    if not data:
        return "Ignored", 200
        
    sender_id = data['sender']
    incoming_msg = data['text'].lower().strip()
    
    # Skip if empty
    if not incoming_msg: return "OK", 200

    # Logic Reuse (Text Processing)
    cleaned_input = incoming_msg.replace("!","").replace(".","")
    
    # 3. ROBUST OVERRIDES (Same as Web)
    if "சின்னம்மை" in cleaned_input or "chinnammai" in cleaned_input:
        cleaned_input = "chicken pox"

    # 4. Find Info
    info = find_topic_info(cleaned_input)
    
    if info:
        topic, desc, precs, img_url = info
        clean_desc = desc
        clean_precs = "\n".join([f"- {p}" for p in precs])
        
        reply_text = f"*ℹ️ Information: {topic.title()}*\n\n{clean_desc}\n\n*Health Safety Awareness:*\n{clean_precs}\n\n⚠️ _Disclaimer: Educational info only. Not a diagnosis._"
        send_whatsapp_message(sender_id, reply_text)
        
        # if img_url: send_image... (Simulate via text for now or extend service)
        
        save_interaction(incoming_msg, reply_text, "whatsapp_info", 1.0, "WhatsApp")
        
    else:
        # Fallback
        groq_resp = get_ai_explanation(cleaned_input, "English")
        if groq_resp and ("what is" in incoming_msg or "define" in incoming_msg):
             reply_text = f"*Definition:*\n{groq_resp}\n\n⚠️ _General Info Only._"
             send_whatsapp_message(sender_id, reply_text)
             save_interaction(incoming_msg, groq_resp, "whatsapp_ai", 0.5, "WhatsApp")
        else:
             reply_text = "I am a Public Health Bot. Ask me about 'Malaria', 'Dengue' or 'Vaccinations'.\n\n_I do not diagnose conditions._"
             send_whatsapp_message(sender_id, reply_text)
             save_interaction(incoming_msg, "Fallback Help", "whatsapp_unclear", 0.0, "WhatsApp")
        
    return "OK", 200


def format_ai_response(text):
    if not text: return ""
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = text.replace("\n", "<br>")
    return text

def save_interaction(user_text, bot_html, intent, conf, region=None):
    """Helper to log interactions to the DB safely."""
    try:
        u_identifier = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        with app.app_context(): # Ensure we are in context
            user = User.query.filter_by(user_identifier=u_identifier).first()
            if not user:
                user = User(user_identifier=u_identifier)
                db.session.add(user)
                db.session.commit()
                
            interaction = Interaction(
                user_id=user.id,
                user_message=user_text,
                bot_response=bot_html, 
                intent_detected=intent,
                confidence_score=float(conf),
                region=region, # Store simulated or real region
                sentiment="neutral" 
            )
            db.session.add(interaction)
            db.session.commit()
    except Exception as e:
        print(f"⚠️ DB LOGGING FAILED: {e}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

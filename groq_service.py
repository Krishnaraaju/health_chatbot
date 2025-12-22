
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API CONFIG
API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def get_ai_explanation(disease_name, language="English"):
    """
    Fetches a natural language explanation and precautions for the disease using Groq API.
    """

    # 1. Fast Local Fallback for Tamil
    if language == "Tamil":
        tamil_map = {
            "Chikungunya": "சிக்குன்குனியா",
            "Dengue": "டெங்கு காய்ச்சல்",
            "Fungal infection": "பூஞ்சை தொற்று",
            "Common Cold": "சாதாரண சளி",
            "Typhoid": "டைபாய்டு",
            "Malaria": "மலேரியா",
            "Viral Fever": "வைரஸ் காய்ச்சல்",
            "Depression": "மன அழுத்தம்",
            "Depression (Chronic)": "நாள்பட்ட மன அழுத்தம்",
            "Rosacea": "ரோசாசியா",
            "Stomach Pain": "வயிற்று வலி",
            "Heart Attack": "மாரடைப்பு",
            "Fibromyalgia": "உடல் தசை வலி",
            "Diabetes": "சர்க்கரை நோய்",
            "Hypertension": "உயர் ரத்த அழுத்தம்",
            "Migraine": "ஒற்றை தலைவலி",
            "Jaundice": "மஞ்சள் காமாலை",
            "Pneumonia": "நுரையீரல் அழற்சி",
            "Arthritis": "மூட்டு வலி"
        }
        
        t_name = disease_name
        for k, v in tamil_map.items():
            if k.lower() in disease_name.lower():
                t_name = v
                break
        
        return f"""<b>{t_name}</b><br><br>
        இது ஒரு மருத்துவ நிலை. உரிய சிகிச்சை தேவை.<br><br>
        <b>முன்னெச்சரிக்கைகள்:</b><br>
        1. மருத்துவரை அணுகவும்<br>
        2. ஓய்வு எடுக்கவும்<br>
        3. மருந்து உட்கொள்ளவும்"""

    if not API_KEY:
        print("Error: GROQ_API_KEY not found in environment variables.")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are Swasthya Sahayak, a helpful medical informational AI.
    The user is asking about symptoms that are commonly associated with: "{disease_name}".
    
    1. Explain "{disease_name}" in simple, easy-to-understand {language}.
    2. Provide 3-4 distinct numeric bullet points for general care in {language}.
    3. Be brief but informative (max 100 words).
    
    CRITICAL SAFETY RULES:
    - NEVER say "You have {disease_name}".
    - NEVER say "I diagnose you with...".
    - ALWAYS say "These symptoms are often associated with..." or "This condition is..."
    - Do not give specific dosage instructions.
    - Mention that this is for information only."""
    
    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "llama-3.3-70b-versatile", 
        "temperature": 0.5,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 400:
             print(f"Groq 400 Error Details: {response.text}")
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
            
    except Exception as e:
        print(f"Groq API Error: {e}")
        return None


from deep_translator import GoogleTranslator

def translate_to_english(text, source_language="auto"):
    """
    Translates user input to English using Google Translate (deep-translator).
    """
    print(f"Translating ({source_language}): {text}...")
    
    # 0. Local Map (Expanded for common tanglish/hinglish)
    local_map = {
        "kaichal": "fever",
        "juram": "fever",
        "bukhar": "fever",
        "sardi": "cold",
        "irumal": "cough",
        "khansi": "cough",
        "pet dard": "stomach pain",
        "vayitru vali": "stomach pain",
        "sar dard": "headache",
        "thalai vali": "headache"
    }
    
    if text.lower() in local_map:
        return local_map[text.lower()]
        
    try:
        # Google Translate
        translator = GoogleTranslator(source='auto', target='en')
        translation = translator.translate(text)
        print(f"Google Translated: '{text}' -> '{translation}'")
        return translation
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

def translate_message(text, target_lang):
    """
    Translates English response to User Language using Google Translate.
    """
    if target_lang == "English": return text
    
    # Map friendly names to ISO codes
    lang_map = {
        "Tamil": "ta",
        "Hindi": "hi",
        "Odia": "or",
        "Telugu": "te",
        "Malayalam": "ml",
        "Kannada": "kn"
    }
    iso_code = lang_map.get(target_lang, "en")
    
    try:
        translator = GoogleTranslator(source='en', target=iso_code)
        # Handle HTML tags loosely (deep-translator maintains them mostly)
        translation = translator.translate(text)
        return translation
    except Exception as e:
        print(f"Response Translation Error: {e}")
        return text

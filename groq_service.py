
import os
import json
import requests
from deep_translator import GoogleTranslator
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

    # Tamil fallback removed: handled by main app via Google Translate or Offline CSVs.

    if not API_KEY:
        print("Error: GROQ_API_KEY not found in environment variables.")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are Swasthya Sahayak, a public health informational AI.
    The user asked: "{disease_name}".

    TASK:
    1. First, determine if "{disease_name}" is a medical condition, symptom, or health-related topic.
    2. IF IT IS NOT HEALTH-RELATED (e.g., Cricket, Movies, Politics, Coding):
       - Respond: "I am a health assistant. '{disease_name}' is [brief definition], but this is not a medical topic. Please ask me about symptoms, diseases, or vaccinations."
       - STOP there. Do not list symptoms or treatments.

    3. IF IT IS HEALTH-RELATED:
       - Explain it in simple {language}.
       - Provide 3-4 distinct numeric bullet points for general care/prevention in {language}.
       - Be brief (max 100 words).

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

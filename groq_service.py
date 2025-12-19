
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
    
    prompt = f"""You are Swasthya Sahayak, a compassionate medical AI.
    The user has been recognized with specific symptoms matching: "{disease_name}".
    
    1. Explain "{disease_name}" in simple, easy-to-understand {language}.
    2. Provide 3-4 distinct numeric bullet points for critical precautions/home remedies in {language}.
    3. Be brief but informative (max 100 words).
    
    Do not mention you are an AI. Just give the helpful information."""
    
    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "llama-3.1-8b-instant", 
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


def translate_to_english(text, source_language):
    """
    Translates user input to English for the ML model.
    """
    print(f"Translating from {source_language}: {text}...")
    
    if source_language == "Tamil":
        text_map = {
            "காய்ச்சல்": "fever",
            "தலைவலி": "headache",
            "வாந்தி": "vomiting",
            "இருமல்": "cough",
            "சளி": "cold",
            "வயிற்று வலி": "stomach pain"
        }
        for k, v in text_map.items():
            if k in text:
                text = text.replace(k, v)
                return text

    if not API_KEY:
        print("Skipping translation (No API Key)")
        return text

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Translate the following {source_language} health query into simple English keywords.
    Original: "{text}"
    Translation (English only, no extra text):"""
    
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "llama3-8b-8192",
        "temperature": 0.0
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        translation = result['choices'][0]['message']['content'].strip()
        print(f"Translated: {translation}")
        return translation
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

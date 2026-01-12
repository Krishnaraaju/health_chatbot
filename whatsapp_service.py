import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# CONFIG
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = "v17.0"

def send_whatsapp_message(to_number, message_body):
    """
    Sends a text message to a WhatsApp user via Meta Cloud API.
    """
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_body
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending WhatsApp message: {e}")
        if e.response:
            print(f"Response: {e.response.text}")
        return None

def process_webhook_payload(payload):
    """
    Extracts relevant info (sender, message) from the webhook payload.
    Returns None if validation fails or not a user message.
    """
    try:
        entry = payload['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' in value:
            message = value['messages'][0]
            sender_id = message['from']
            text_body = ""
            
            if message['type'] == 'text':
                text_body = message['text']['body']
            else:
                text_body = "[Media/Non-text message]"
                
            return {
                "sender": sender_id,
                "text": text_body,
                "timestamp": message['timestamp']
            }
            
    except (KeyError, IndexError):
        pass
        
    return None

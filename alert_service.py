
import feedparser
from datetime import datetime
import json
import os

def get_health_alerts():
    """
    Fetches real-time health alerts from trusted RSS feeds (WHO, Google Health)
    AND manual alerts from the Admin Portal.
    """
    alerts = []
    
    # 0. Load Manual Alerts (High Priority)
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "Data", "manual_alerts.json")
        
        if os.path.exists(json_path):
            with open(json_path, "r", encoding='utf-8') as f:
                manual_data = json.load(f)
                
            # If it's a list (multiple alerts) or dict (single active alert wrapper)
            # Let's assume list for now
            if isinstance(manual_data, list):
                for m in manual_data:
                    if m.get('active', True):
                        alerts.append({
                            "title": m.get("title", "System Alert"),
                            "link": "#",
                            "source": "📢 Official Broadcast",
                            "published": m.get("date", datetime.now().strftime("%d %b")),
                            "summary": m.get("message", ""),
                            "class": "manual-alert"
                        })
    except Exception as e:
        print(f"Manual Alert Load Error: {e}")

    # 1. RSS Feed URLs (Verified Sources)
    rss_urls = [
        "https://www.who.int/feeds/entity/csr/don/en/rss.xml", # WHO Disease Outbreak News
        "https://news.google.com/rss/search?q=disease+outbreak+india&hl=en-IN&gl=IN&ceid=IN:en" # Google News (India Health)
    ]
    
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:3]: # Get top 3 from each
                # Basic Keyword Filter for Safety
                keywords = ["outbreak", "virus", "infection", "alert", "emergency", "dengue", "malaria", "covid"]
                title_lower = entry.title.lower()
                
                if any(k in title_lower for k in keywords):
                    alerts.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": feed.feed.title if 'title' in feed.feed else "News",
                        "published": entry.published if 'published' in entry else datetime.now().strftime("%d %b %Y")
                    })
                    
        except Exception as e:
            print(f"RSS Error ({url}): {e}")
            
    return alerts[:5] # Return top 5 combined

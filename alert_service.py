
import feedparser
from datetime import datetime

def get_health_alerts():
    """
    Fetches real-time health alerts from trusted RSS feeds (WHO, Google Health).
    Returns a list of structured alerts.
    """
    # RSS Feed URLs (Verified Sources)
    rss_urls = [
        "https://www.who.int/feeds/entity/csr/don/en/rss.xml", # WHO Disease Outbreak News
        "https://news.google.com/rss/search?q=disease+outbreak+india&hl=en-IN&gl=IN&ceid=IN:en" # Google News (India Health)
    ]
    
    alerts = []
    
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

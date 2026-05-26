"""Monitor mode: track price changes for a list of URLs."""
from card import run_card
from stealth import random_delay
import json
from datetime import datetime

def run_monitor(proxy_url, urls):
    """Run monitor mode: fetch current prices and compare with previous."""
    print(f"Monitoring {len(urls)} URLs")
    
    # Fetch current state
    current_cards = run_card(proxy_url, urls)
    
    # Build result with timestamp
    result = {
        "checked_at": datetime.utcnow().isoformat(),
        "total_urls": len(urls),
        "successful": 0,
        "failed": 0,
        "cards": []
    }
    
    for card in current_cards:
        entry = {
            "url": card.get("url"),
            "title": card.get("title"),
            "current_price": card.get("price"),
            "price_raw": card.get("price_raw"),
            "vin": card.get("vin"),
            "year": card.get("year"),
            "mileage_km": card.get("mileage_km"),
            "location": card.get("location"),
            "error": card.get("error")
        }
        
        if card.get("error"):
            result["failed"] += 1
        else:
            result["successful"] += 1
        
        result["cards"].append(entry)
    
    return result

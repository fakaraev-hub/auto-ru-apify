"""Monitor mode: track price changes for a list of URLs."""
from card import run_card
from datetime import datetime


def run_monitor(proxy_url, urls, debug_page=False):
    """Run monitor mode. Returns (result_dict, last_page_ref_or_None)."""
    print(f"Monitoring {len(urls)} URLs")

    current_cards, page_ref = run_card(proxy_url, urls, debug_page=debug_page)

    result = {
        'checked_at': datetime.utcnow().isoformat(),
        'total_urls': len(urls),
        'successful': 0,
        'failed': 0,
        'cards': [],
    }

    for card in current_cards:
        entry = {
            'url': card.get('url'),
            'title': card.get('title'),
            'current_price': card.get('price'),
            'price_raw': card.get('price_raw'),
            'vin': card.get('vin'),
            'year': card.get('year'),
            'mileage_km': card.get('mileage_km'),
            'location': card.get('location'),
            'error': card.get('error'),
        }
        if card.get('error'):
            result['failed'] += 1
        else:
            result['successful'] += 1
        result['cards'].append(entry)

    return result, page_ref

"""Card mode: parse single auto.ru offer page."""
import re
import json
from bs4 import BeautifulSoup
from stealth import create_browser, random_delay, handle_geo_block

BASE_URL = "https://auto.ru"

def parse_card_page(page_content, url):
    """Parse offer card HTML."""
    soup = BeautifulSoup(page_content, 'lxml')
    card = {"url": url, "parsed_at": None}
    
    # Title (brand model year)
    title_el = soup.find('h1')
    if title_el:
        card['title'] = title_el.get_text(strip=True)
    
    # Price
    price_el = soup.find('span', class_=re.compile('OfferPriceCaption__price'))
    if not price_el:
        price_el = soup.find('div', class_=re.compile('PriceOffer'))
    if price_el:
        price_text = price_el.get_text(strip=True)
        digits = re.findall(r'[\d\s]+', price_text)
        if digits:
            card['price'] = int(''.join(digits[0].split()))
            card['price_raw'] = price_text
    
    # VIN
    vin_el = soup.find(string=re.compile(r'VIN|вин', re.I))
    if vin_el:
        parent = vin_el.find_parent()
        if parent:
            vin_text = parent.get_text()
            vin_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', vin_text, re.I)
            if vin_match:
                card['vin'] = vin_match.group().upper()
    
    # Also try meta/JSON
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if 'vehicleIdentificationNumber' in data:
                    card['vin'] = data['vehicleIdentificationNumber']
                if 'offers' in data and isinstance(data['offers'], dict):
                    card['price'] = data['offers'].get('price', card.get('price'))
                    card['currency'] = data['offers'].get('priceCurrency', 'RUB')
        except:
            pass
    
    # Specifications table
    specs = {}
    spec_rows = soup.find_all('div', class_=re.compile('CardInfoRow'))
    for row in spec_rows:
        label_el = row.find('span', class_=re.compile('CardInfoRow__cell'))
        value_el = row.find_all('span', class_=re.compile('CardInfoRow__cell'))
        if len(value_el) >= 2 and label_el:
            label = label_el.get_text(strip=True)
            value = value_el[1].get_text(strip=True)
            specs[label] = value
    
    # Common fields
    field_mapping = {
        'Год выпуска': 'year',
        'Пробег': 'mileage',
        'Кузов': 'body_type',
        'Цвет': 'color',
        'Двигатель': 'engine',
        'Коробка': 'transmission',
        'Привод': 'drive',
        'Руль': 'steering',
        'Состояние': 'condition',
        'Владельцы': 'owners_count',
        'ПТС': 'pts',
        'Таможня': 'customs',
    }
    
    for ru_label, en_key in field_mapping.items():
        if ru_label in specs:
            card[en_key] = specs[ru_label]
    
    # Extract numeric values
    if 'mileage' in card:
        digits = re.findall(r'[\d\s]+', card['mileage'])
        if digits:
            card['mileage_km'] = int(''.join(digits[0].split()))
    
    if 'year' in card and isinstance(card['year'], str):
        year_match = re.search(r'\d{4}', card['year'])
        if year_match:
            card['year'] = int(year_match.group())
    
    if 'owners_count' in card:
        num_match = re.search(r'\d+', card['owners_count'])
        if num_match:
            card['owners_count'] = int(num_match.group())
    
    # Seller info
    seller_el = soup.find('div', class_=re.compile('SellerInfo'))
    if seller_el:
        name_el = seller_el.find('div', class_=re.compile('SellerInfo__name'))
        if name_el:
            card['seller_name'] = name_el.get_text(strip=True)
        
        phone_el = seller_el.find('button', class_=re.compile('ShowPhoneButton'))
        if phone_el:
            card['phone_button'] = True
    
    # Location
    location_el = soup.find('span', class_=re.compile('MetroList'))
    if not location_el:
        location_el = soup.find('div', class_=re.compile('OfferCard__location'))
    if location_el:
        card['location'] = location_el.get_text(strip=True)
    
    # Photos
    photos = []
    img_els = soup.find_all('img', class_=re.compile('ImageGallery__image'))
    for img in img_els[:10]:  # limit to 10
        src = img.get('src') or img.get('data-src')
        if src and 'autoru' in src:
            photos.append(src)
    card['photos'] = photos
    
    # Description
    desc_el = soup.find('div', class_=re.compile('CardDescription__text'))
    if desc_el:
        card['description'] = desc_el.get_text(strip=True)
    
    return card

def run_card(proxy_url, urls, debug_page=False):
    """Run card mode. Returns (cards, last_page_ref_or_None)."""
    browser, page = create_browser(proxy_url)

    try:
        all_cards = []
        last_page = None

        for url in urls:
            print(f"Parsing: {url}")

            for attempt in range(3):
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    random_delay(1000, 2000)
                    handle_geo_block(page)
                    random_delay(500, 1500)
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {e}")
                    if attempt == 2:
                        all_cards.append({'url': url, 'error': str(e)})
                        continue
                    random_delay(2000, 5000)

            for _ in range(5):
                page.evaluate('window.scrollBy(0, window.innerHeight)')
                random_delay(800, 2000)

            last_page = page
            content = page.content()
            card = parse_card_page(content, url)
            all_cards.append(card)
            print(f"Card parsed: {card.get('title', 'N/A')} — {card.get('price', 'N/A')} ₽")

            random_delay(3000, 6000)

        return all_cards, (last_page if debug_page else None)

    finally:
        if not debug_page:
            browser.close()

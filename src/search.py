"""Search mode: scrape auto.ru listings from search results."""
import re
import json
from bs4 import BeautifulSoup
from .stealth import create_stealth_context, random_delay

BASE_URL = "https://auto.ru"

def build_search_url(brand, model, price_min, price_max, year_min, year_max, city):
    """Build auto.ru search URL from filters."""
    params = []
    
    if brand:
        brand_slug = brand.lower().replace(" ", "_")
        params.append(f"mark={brand_slug.upper()}")
    
    if model:
        model_slug = model.lower().replace(" ", "_")
        params.append(f"model={model_slug.upper()}")
    
    if price_min > 0:
        params.append(f"price_from={price_min}")
    
    if price_max > 0:
        params.append(f"price_to={price_max}")
    
    if year_min > 0:
        params.append(f"year_from={year_min}")
    
    if year_max > 0:
        params.append(f"year_to={year_max}")
    
    if city:
        city_slug = city.lower()
        params.append(f"geo_id={city_slug}")
    
    query = "&".join(params) if params else ""
    return f"{BASE_URL}/moskva/cars/{brand.lower()}/{model.lower()}/all/?{query}" if brand else f"{BASE_URL}/moskva/cars/all/?{query}"

def parse_search_page(page_content):
    """Parse search results HTML."""
    soup = BeautifulSoup(page_content, 'lxml')
    listings = []
    
    # auto.ru listing cards
    items = soup.find_all('div', class_=re.compile('ListingItem'))
    
    for item in items:
        listing = {}
        
        # Title
        title_el = item.find('a', class_=re.compile('ListingItemTitle'))
        if title_el:
            listing['title'] = title_el.get_text(strip=True)
            listing['url'] = title_el.get('href', '')
        
        # Price
        price_el = item.find('div', class_=re.compile('ListingItemPrice'))
        if price_el:
            price_text = price_el.get_text(strip=True)
            # Extract digits
            digits = re.findall(r'[\d\s]+', price_text)
            if digits:
                listing['price_raw'] = price_text
                listing['price'] = int(''.join(digits[0].split()))
        
        # Year
        year_el = item.find('div', class_=re.compile('ListingItemYear'))
        if year_el:
            year_text = year_el.get_text(strip=True)
            year_match = re.search(r'\d{4}', year_text)
            if year_match:
                listing['year'] = int(year_match.group())
        
        # Mileage
        mileage_el = item.find('div', class_=re.compile('ListingItemKmAge'))
        if mileage_el:
            mileage_text = mileage_el.get_text(strip=True)
            digits = re.findall(r'[\d\s]+', mileage_text)
            if digits:
                listing['mileage_raw'] = mileage_text
                listing['mileage_km'] = int(''.join(digits[0].split()))
        
        # Location
        location_el = item.find('span', class_=re.compile('MetroList'))
        if location_el:
            listing['location'] = location_el.get_text(strip=True)
        
        # Image
        img_el = item.find('img')
        if img_el:
            listing['image'] = img_el.get('src', '') or img_el.get('data-src', '')
        
        # Seller type
        seller_el = item.find('div', class_=re.compile('ListingItem__salon'))
        listing['seller_type'] = 'dealer' if seller_el else 'private'
        
        if listing.get('title') and listing.get('price'):
            listings.append(listing)
    
    return listings

def run_search(proxy_url, search_url=None, brand="", model="", price_min=0, price_max=0, 
               year_min=0, year_max=0, city="", max_pages=3):
    """Run search mode and return listings."""
    p, browser, context, page = create_stealth_context(proxy_url)
    
    try:
        # Build URL
        url = search_url or build_search_url(brand, model, price_min, price_max, year_min, year_max, city)
        print(f"Searching: {url}")
        
        all_listings = []
        
        for page_num in range(1, max_pages + 1):
            page_url = f"{url}&page={page_num}" if page_num > 1 else url
            
            # Navigate with retry
            for attempt in range(3):
                try:
                    page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                    random_delay(1000, 3000)
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {e}")
                    if attempt == 2:
                        raise
                    random_delay(2000, 5000)
            
            # Scroll to load lazy content
            for _ in range(3):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                random_delay(500, 1500)
            
            content = page.content()
            listings = parse_search_page(content)
            print(f"Page {page_num}: found {len(listings)} listings")
            
            if not listings:
                break
            
            all_listings.extend(listings)
            
            # Check for next page
            next_btn = page.query_selector('[class*="ListingPagination__next"]')
            if not next_btn or next_btn.is_hidden():
                break
            
            random_delay(2000, 4000)
        
        return all_listings
        
    finally:
        context.close()
        browser.close()
        p.stop()

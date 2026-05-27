"""Search mode: scrape auto.ru listings from search results."""
import re
import json
from bs4 import BeautifulSoup
from stealth import create_browser, random_delay

BASE_URL = "https://auto.ru"


def build_search_url(brand, model, price_min, price_max, year_min, year_max, city):
    """Build auto.ru search URL from filters."""
    parts = []
    brand_slug = brand.lower().replace(' ', '_') if brand else ''
    model_slug = model.lower().replace(' ', '_') if model else ''

    if brand_slug and model_slug:
        path = f"/moskva/cars/{brand_slug}/{model_slug}/all/"
    elif brand_slug:
        path = f"/moskva/cars/{brand_slug}/all/"
    else:
        path = "/moskva/cars/all/"

    params = []
    if price_min > 0: params.append(f"price_from={price_min}")
    if price_max > 0: params.append(f"price_to={price_max}")
    if year_min > 0:  params.append(f"year_from={year_min}")
    if year_max > 0:  params.append(f"year_to={year_max}")

    qs = '?' + '&'.join(params) if params else ''
    return f"{BASE_URL}{path}{qs}"


def parse_listing_item(item):
    """Extract listing data from a single card element (BeautifulSoup tag)."""
    listing = {}

    # Title — try multiple selector patterns
    for sel in [
        lambda e: e.find('a', class_=re.compile(r'ListingItemTitle|listingItem.*title', re.I)),
        lambda e: e.find('h3'),
        lambda e: e.find('a', {'data-auto': re.compile(r'title|name', re.I)}),
    ]:
        el = sel(item)
        if el:
            listing['title'] = el.get_text(strip=True)
            href = el.get('href', '')
            if href:
                listing['url'] = href if href.startswith('http') else BASE_URL + href
            break

    # Price
    for sel in [
        lambda e: e.find(class_=re.compile(r'ListingItemPrice|price', re.I)),
        lambda e: e.find(attrs={'data-auto': re.compile(r'price', re.I)}),
    ]:
        el = sel(item)
        if el:
            price_text = el.get_text(strip=True)
            digits = re.findall(r'[\d\s]+', price_text)
            if digits:
                listing['price_raw'] = price_text
                try:
                    listing['price'] = int(''.join(digits[0].split()))
                except ValueError:
                    pass
            break

    # Year
    for sel in [
        lambda e: e.find(class_=re.compile(r'Year|year', re.I)),
        lambda e: e.find(attrs={'data-auto': 'year'}),
    ]:
        el = sel(item)
        if el:
            m = re.search(r'\d{4}', el.get_text())
            if m:
                listing['year'] = int(m.group())
            break

    # Mileage
    for sel in [
        lambda e: e.find(class_=re.compile(r'KmAge|mileage|km', re.I)),
        lambda e: e.find(attrs={'data-auto': re.compile(r'mileage|km', re.I)}),
    ]:
        el = sel(item)
        if el:
            text = el.get_text(strip=True)
            digits = re.findall(r'[\d\s]+', text)
            if digits:
                listing['mileage_raw'] = text
                try:
                    listing['mileage_km'] = int(''.join(digits[0].split()))
                except ValueError:
                    pass
            break

    # Location
    for sel in [
        lambda e: e.find(class_=re.compile(r'MetroList|location|Location', re.I)),
        lambda e: e.find(attrs={'data-auto': re.compile(r'location|metro', re.I)}),
    ]:
        el = sel(item)
        if el:
            listing['location'] = el.get_text(strip=True)
            break

    # Seller type
    dealer_el = item.find(class_=re.compile(r'salon|dealer|Salon|Dealer', re.I))
    listing['seller_type'] = 'dealer' if dealer_el else 'private'

    return listing if listing.get('title') or listing.get('price') else None


def find_listing_items(soup):
    """Try multiple strategies to find listing card elements."""
    # Strategy 1: class contains 'ListingItem'
    items = soup.find_all('div', class_=re.compile(r'ListingItem'))
    if items:
        return items, 'class~ListingItem'

    # Strategy 2: data-auto=listingItem
    items = soup.find_all(attrs={'data-auto': 'listingItem'})
    if items:
        return items, 'data-auto=listingItem'

    # Strategy 3: data-auto contains 'snippet' or 'item'
    items = soup.find_all(attrs={'data-auto': re.compile(r'snippet|listing', re.I)})
    if items:
        return items, 'data-auto~snippet'

    # Strategy 4: article tags
    items = soup.find_all('article')
    if items:
        return items, 'article'

    return [], 'none'


def parse_search_page(page_content):
    """Parse search results HTML. Returns (listings, selector_used)."""
    soup = BeautifulSoup(page_content, 'lxml')
    items, selector_used = find_listing_items(soup)

    listings = []
    for item in items:
        data = parse_listing_item(item)
        if data:
            listings.append(data)

    return listings, selector_used


def run_search(proxy_url, search_url=None, brand='', model='', price_min=0, price_max=0,
               year_min=0, year_max=0, city='', max_pages=3, debug_page=False):
    """Run search mode. Returns (listings, last_page_ref_or_None)."""
    browser, page = create_browser(proxy_url)

    try:
        url = search_url or build_search_url(brand, model, price_min, price_max, year_min, year_max, city)
        print(f"Searching: {url}")

        all_listings = []
        last_page = None

        for page_num in range(1, max_pages + 1):
            page_url = f"{url}&page={page_num}" if page_num > 1 else url

            for attempt in range(3):
                try:
                    page.goto(page_url, wait_until='domcontentloaded', timeout=30000)
                    random_delay(1000, 3000)
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {e}")
                    if attempt == 2:
                        raise
                    random_delay(2000, 5000)

            # Scroll to trigger lazy loading
            for _ in range(3):
                page.evaluate('window.scrollBy(0, window.innerHeight)')
                random_delay(500, 1500)

            last_page = page
            content = page.content()
            listings, selector = parse_search_page(content)
            print(f"Page {page_num}: {len(listings)} listings (selector: {selector}), url_final={page.url}")

            if not listings:
                # Log title to help debug empty results
                print(f"  Page title: {page.title()}")
                break

            all_listings.extend(listings)

            # Next page
            next_btn = page.query_selector('[class*="ListingPagination__next"], [data-auto="pagination-next"]')
            if not next_btn or next_btn.is_hidden():
                break

            random_delay(2000, 4000)

        return all_listings, (last_page if debug_page else None)

    finally:
        if not debug_page:
            browser.close()
        else:
            # Caller will close after debug save
            pass

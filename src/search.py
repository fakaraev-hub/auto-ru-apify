"""Search mode: scrape auto.ru listings from search results."""
import re
import json
from bs4 import BeautifulSoup
from stealth import create_browser, random_delay, handle_geo_block

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
    """Extract listing data from a single card element (BeautifulSoup tag).

    Selectors verified 2026-05-27 against live auto.ru HTML (CloakBrowser + Apify Residential RU).
    Card container: div.ListingItemUniversal-* (dash suffix, not double-underscore children).
    """
    listing = {}

    # Title + URL — BEM class ListingItemTitle__link is stable
    title_el = item.find('a', class_=re.compile(r'ListingItemTitle__link'))
    if title_el:
        listing['title'] = title_el.get_text(strip=True)
        href = title_el.get('href', '')
        if href:
            listing['url'] = href if href.startswith('http') else BASE_URL + href

    # Price — ListingItemUniversal__price-* (strip trailing "Справедливая цена" text)
    price_el = item.find(class_=re.compile(r'ListingItemUniversal__price'))
    if price_el:
        price_text = price_el.get_text(strip=True)
        digits = re.findall(r'[\d\s]+', price_text)
        if digits:
            listing['price_raw'] = price_text
            try:
                listing['price'] = int(''.join(digits[0].split()))
            except ValueError:
                pass

    # Year — Typography2__h5 contains the 4-digit year
    year_el = item.find(class_=re.compile(r'Typography2__h5'))
    if year_el:
        m = re.search(r'\b(19|20)\d{2}\b', year_el.get_text())
        if m:
            listing['year'] = int(m.group())

    # Mileage — ListingItemUniversalCondition__status contains "N *** км"
    mileage_el = item.find(class_=re.compile(r'ListingItemUniversalCondition__status'))
    if mileage_el:
        text = mileage_el.get_text(strip=True)
        digits = re.findall(r'[\d\s]+', text)
        if digits:
            listing['mileage_raw'] = text
            try:
                listing['mileage_km'] = int(''.join(digits[0].split()))
            except ValueError:
                pass

    # Location — MetroListPlace__regionName holds city name
    loc_el = item.find(class_=re.compile(r'MetroListPlace__regionName'))
    if loc_el:
        listing['location'] = loc_el.get_text(strip=True)

    # Seller name
    seller_el = item.find(class_=re.compile(r'ListingItemUniversalSeller__sellerName'))
    if seller_el:
        listing['seller_name'] = seller_el.get_text(strip=True)

    # Dealer flag — SalonVerifiedLabel appears only on verified dealers
    dealer_el = item.find(class_=re.compile(r'SalonVerifiedLabel|ListingItemUniversalSeller__salonVerified'))
    listing['seller_type'] = 'dealer' if dealer_el else 'private'

    return listing if listing.get('title') or listing.get('price') else None


def find_listing_items(soup):
    """Find listing card container elements.

    Selectors verified 2026-05-27. Strategy order: most specific first.
    Each card root has class ListingItemUniversal-<hash> (dash, not __),
    which differs from child elements using ListingItemUniversal__<block>-<hash>.
    """
    # Strategy 1: ListingItemUniversal-* root containers (verified primary selector)
    items = [el for el in soup.find_all('div') if any(
        re.match(r'^ListingItemUniversal-', c) for c in el.get('class', [])
    )]
    if items:
        return items, 'ListingItemUniversal-root'

    # Strategy 2: data-auto=listingItem fallback
    items = soup.find_all(attrs={'data-auto': 'listingItem'})
    if items:
        return items, 'data-auto=listingItem'

    # Strategy 3: article tags fallback
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

            for attempt in range(5):
                try:
                    page.goto(page_url, wait_until='domcontentloaded', timeout=60000)
                    final_url = page.url
                    if not final_url.startswith('https://') or 'chrome-error' in final_url:
                        raise Exception(f"Bad URL after navigation: {final_url}")
                    random_delay(1000, 2000)
                    handle_geo_block(page)
                    random_delay(500, 1000)
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {e}")
                    if attempt == 4:
                        raise
                    random_delay(3000, 7000)

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

            # Deduplicate by URL within this batch before extending
            seen_urls = {l['url'] for l in all_listings if l.get('url')}
            new_listings = [l for l in listings if l.get('url') not in seen_urls or not l.get('url')]
            print(f"  Unique new: {len(new_listings)} (filtered {len(listings)-len(new_listings)} dupes)")
            all_listings.extend(new_listings)

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

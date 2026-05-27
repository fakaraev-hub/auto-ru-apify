"""CloakBrowser context factory — replaces Playwright stealth layer."""
import random
from cloakbrowser import launch


def create_browser(proxy_url=None):
    """Launch a CloakBrowser instance with a random fingerprint seed.

    Returns (browser, page). Caller must call browser.close() in finally.
    """
    seed = random.randint(10000, 99999)
    browser = launch(
        headless=True,
        proxy=proxy_url or None,
        args=[f"--fingerprint={seed}"],
    )
    page = browser.new_page()
    return browser, page


def handle_geo_block(page):
    """Detect and dismiss auto.ru geo-restriction page ('Сайт не предназначен для вашего региона').

    The block is an <a id="confirm-button" href="/gdpr/confirm/?retpath=..."> link.
    We navigate directly to that href instead of simulating a click.
    Returns True if the block was found and dismissed.
    """
    try:
        el = page.query_selector('#confirm-button')
        if el:
            href = el.get_attribute('href')
            if href and 'gdpr' in href:
                print(f"Geo-block detected — navigating to GDPR confirm URL")
                page.goto(href, wait_until='domcontentloaded', timeout=15000)
                page.wait_for_load_state('networkidle', timeout=10000)
                return True
    except Exception as e:
        print(f"handle_geo_block error: {e}")
    return False


def random_delay(min_ms=500, max_ms=3000):
    import time
    time.sleep(random.uniform(min_ms, max_ms) / 1000)

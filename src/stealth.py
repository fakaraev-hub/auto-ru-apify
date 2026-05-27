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

    Returns True if the block was found and dismissed.
    """
    try:
        btn = page.query_selector('.button_blue, button.button_blue')
        if btn:
            text = btn.inner_text(timeout=2000).strip()
            if 'согласен' in text or 'agree' in text.lower():
                print("Geo-block detected — clicking 'Я согласен'")
                btn.click()
                page.wait_for_load_state('domcontentloaded', timeout=10000)
                return True
    except Exception:
        pass
    return False


def random_delay(min_ms=500, max_ms=3000):
    import time
    time.sleep(random.uniform(min_ms, max_ms) / 1000)

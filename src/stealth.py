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


def random_delay(min_ms=500, max_ms=3000):
    import time
    time.sleep(random.uniform(min_ms, max_ms) / 1000)

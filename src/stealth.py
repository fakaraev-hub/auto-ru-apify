"""Anti-detection layer for auto.ru scraping."""
import random
from playwright.sync_api import sync_playwright

def create_stealth_context(proxy_url=None):
    """Create a stealth browser context with randomized fingerprint."""
    p = sync_playwright().start()
    
    # Randomize viewport (common desktop resolutions)
    viewports = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 1280, "height": 720},
    ]
    vp = random.choice(viewports)
    
    # Launch browser
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
    ]
    
    browser = p.chromium.launch(
        headless=True,
        args=args,
        proxy={"server": proxy_url} if proxy_url else None,
    )
    
    context = browser.new_context(
        viewport=vp,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        locale="ru-RU",
        timezone_id="Europe/Moscow",
        geolocation={"latitude": 55.7558, "longitude": 37.6173},
        permissions=["geolocation"],
        color_scheme="light",
    )
    
    # Create page
    page = context.new_page()
    
    # Additional anti-detection
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
    """)
    
    return p, browser, context, page

def random_delay(min_ms=500, max_ms=3000):
    """Random delay between actions."""
    import time
    delay = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay)

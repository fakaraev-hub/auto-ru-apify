#!/usr/bin/env python3
"""Main entry point for Apify auto.ru actor."""
import sys
import os
import json
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apify_client import ApifyClient

from search import run_search
from card import run_card
from monitor import run_monitor


def get_apify_client():
    token = os.environ.get('APIFY_TOKEN') or os.environ.get('APIFY_API_KEY')
    return ApifyClient(token) if token else None


def push_to_dataset(client, items):
    dataset_id = os.environ.get('APIFY_DEFAULT_DATASET_ID')
    if client and dataset_id and items:
        client.dataset(dataset_id).push_items(items)
        print(f"Pushed {len(items)} items to dataset {dataset_id}")
    else:
        # Fallback: write newline-delimited JSON for local runs
        for item in items:
            print('RESULT:' + json.dumps(item, ensure_ascii=False))


def save_debug_to_kv(client, page, label='debug'):
    """Save screenshot + page HTML to Apify KV store for selector debugging."""
    kv_id = os.environ.get('APIFY_DEFAULT_KEY_VALUE_STORE_ID')
    if not client or not kv_id:
        return
    try:
        screenshot = page.screenshot(full_page=False)
        client.key_value_store(kv_id).set_record(
            key=f'{label}_screenshot',
            value=screenshot,
            content_type='image/png',
        )
        html = page.content()
        client.key_value_store(kv_id).set_record(
            key=f'{label}_html',
            value=html.encode(),
            content_type='text/html; charset=utf-8',
        )
        print(f"Debug saved to KV store: {label}_screenshot, {label}_html")
    except Exception as e:
        print(f"Debug save failed: {e}")


def main():
    input_data = os.environ.get('APIFY_INPUT', '{}')
    try:
        config = json.loads(input_data)
    except Exception:
        config = {}

    mode = config.get('mode', 'search')

    proxy_url = None
    custom_proxy_url = config.get('proxyUrl') or ''
    if custom_proxy_url:
        proxy_url = custom_proxy_url
        print("Using custom proxy URL")
    else:
        proxy_url = os.environ.get('APIFY_PROXY_URL') or None
        if proxy_url:
            print(f"Using Apify proxy: {proxy_url[:40]}...")

    client = get_apify_client()
    debug = config.get('debug', False)

    if mode == 'search':
        results, page_ref = run_search(
            proxy_url=proxy_url,
            search_url=config.get('searchUrl'),
            brand=config.get('brand', ''),
            model=config.get('model', ''),
            price_min=config.get('priceMin', 0),
            price_max=config.get('priceMax', 0),
            year_min=config.get('yearMin', 0),
            year_max=config.get('yearMax', 0),
            city=config.get('city', ''),
            max_pages=config.get('maxPages', 3),
            debug_page=debug,
        )
        if debug and page_ref:
            save_debug_to_kv(client, page_ref, 'search')
        push_to_dataset(client, results)
        print(f"Search complete: {len(results)} listings")

    elif mode == 'card':
        urls = config.get('offerUrls', [])
        if isinstance(urls, str):
            urls = [u.strip() for u in urls.replace('\n', ',').split(',') if u.strip()]
        if not urls and config.get('searchUrl'):
            urls = [config['searchUrl']]

        results, page_ref = run_card(proxy_url=proxy_url, urls=urls, debug_page=debug)
        if debug and page_ref:
            save_debug_to_kv(client, page_ref, 'card')
        push_to_dataset(client, results)
        print(f"Card parsing complete: {len(results)} cards")

    elif mode == 'monitor':
        urls = config.get('offerUrls', [])
        if isinstance(urls, str):
            urls = [u.strip() for u in urls.replace('\n', ',').split(',') if u.strip()]

        result, page_ref = run_monitor(proxy_url=proxy_url, urls=urls, debug_page=debug)
        if debug and page_ref:
            save_debug_to_kv(client, page_ref, 'monitor')
        push_to_dataset(client, [result])
        print(f"Monitor complete: {result['successful']}/{result['total_urls']} URLs checked")

    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == '__main__':
    main()

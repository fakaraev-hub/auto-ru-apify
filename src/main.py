#!/usr/bin/env python3
"""Main entry point for Apify auto.ru actor."""
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search import run_search
from card import run_card
from monitor import run_monitor

def main():
    # Read Apify input
    input_path = os.environ.get('APIFY_INPUT_KEY_VALUE_STORE_PATH', '/tmp/apify_input.json')
    
    # Fallback: read from stdin or file
    if input_path and os.path.isfile(input_path):
        with open(input_path, 'r') as f:
            config = json.load(f)
    else:
        # Try reading from APIFY_INPUT env
        input_data = os.environ.get('APIFY_INPUT', '{}')
        try:
            config = json.loads(input_data)
        except:
            config = {}
    
    # Extract config
    mode = config.get('mode', 'search')
    proxy_config = config.get('proxyConfiguration', {})
    
    # Build proxy URL from Apify proxy config
    proxy_url = None
    if proxy_config.get('useApifyProxy', False):
        proxy_url = os.environ.get('APIFY_PROXY_URL')
        print(f"Using Apify proxy: {proxy_url[:30]}..." if proxy_url else "No proxy configured")
    
    # Run based on mode
    if mode == 'search':
        results = run_search(
            proxy_url=proxy_url,
            search_url=config.get('searchUrl'),
            brand=config.get('brand', ''),
            model=config.get('model', ''),
            price_min=config.get('priceMin', 0),
            price_max=config.get('priceMax', 0),
            year_min=config.get('yearMin', 0),
            year_max=config.get('yearMax', 0),
            city=config.get('city', ''),
            max_pages=config.get('maxPages', 3)
        )
        
        # Output to Apify dataset
        output_path = os.environ.get('APIFY_DEFAULT_DATASET_PATH', '/tmp/output.json')
        with open(output_path, 'w') as f:
            for item in results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"Search complete: {len(results)} listings saved")
        
    elif mode == 'card':
        urls = config.get('offerUrls', [])
        if not urls and config.get('searchUrl'):
            urls = [config['searchUrl']]
        
        results = run_card(proxy_url=proxy_url, urls=urls)
        
        output_path = os.environ.get('APIFY_DEFAULT_DATASET_PATH', '/tmp/output.json')
        with open(output_path, 'w') as f:
            for item in results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"Card parsing complete: {len(results)} cards saved")
        
    elif mode == 'monitor':
        urls = config.get('offerUrls', [])
        result = run_monitor(proxy_url=proxy_url, urls=urls)
        
        output_path = os.environ.get('APIFY_DEFAULT_DATASET_PATH', '/tmp/output.json')
        with open(output_path, 'w') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        print(f"Monitor complete: {result['successful']}/{result['total_urls']} URLs checked")
    
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

if __name__ == '__main__':
    main()

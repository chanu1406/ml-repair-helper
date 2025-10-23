"""
Quick scraper to get REAL market prices for accurate valuations

Uses simple HTTP requests with realistic headers to avoid being blocked.
Focuses on getting JUST the data we need: price and mileage.
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json


def scrape_autotrader(make, model, year=None, max_results=20):
    """
    Scrape Autotrader for real prices

    Autotrader is easier to scrape than Cars.com
    """

    print(f"Scraping Autotrader for: {year or 'any year'} {make} {model}")
    print("-" * 60)

    # Build URL
    base_url = "https://www.autotrader.com/cars-for-sale/all-cars"

    params = {
        'makeCodeList': make.upper(),
        'modelCodeList': model.upper().replace(' ', ''),
        'searchRadius': 0,  # Nationwide
        'zip': '10001',
        'marketExtension': 'include',
        'isNewSearch': 'true',
        'showAccelerateBanner': 'false',
        'sortBy': 'relevance',
        'numRecords': min(max_results, 100)
    }

    if year:
        params['startYear'] = year
        params['endYear'] = year

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Failed to fetch: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all listing cards
        # Autotrader uses data-cmp attributes
        listings = []

        # Try different selectors
        containers = (
            soup.find_all('div', {'data-cmp': 'inventoryListing'}) or
            soup.find_all('div', class_=re.compile('inventory-listing')) or
            soup.find_all('article') or
            soup.find_all('div', class_=re.compile('listing-row'))
        )

        print(f"Found {len(containers)} potential listings")

        for container in containers[:max_results]:
            # Extract price
            price = None
            price_elem = container.find('span', class_=re.compile('price')) or \
                        container.find(text=re.compile(r'\$[0-9,]+'))

            if price_elem:
                price_text = price_elem if isinstance(price_elem, str) else price_elem.get_text()
                price_match = re.search(r'\$([0-9,]+)', price_text)
                if price_match:
                    try:
                        price = int(price_match.group(1).replace(',', ''))
                    except:
                        pass

            # Extract mileage
            mileage = None
            mileage_elem = container.find(text=re.compile(r'[0-9,]+\s*miles?', re.IGNORECASE))
            if mileage_elem:
                mileage_match = re.search(r'([0-9,]+)\s*miles?', mileage_elem, re.IGNORECASE)
                if mileage_match:
                    try:
                        mileage = int(mileage_match.group(1).replace(',', ''))
                    except:
                        pass

            # Extract location
            location = None
            location_elem = container.find(text=re.compile(r'[A-Z][a-z]+,\s*[A-Z]{2}'))
            if location_elem:
                location = location_elem.strip()

            if price:  # Only add if we got a price
                listings.append({
                    'price': price,
                    'mileage': mileage,
                    'location': location,
                    'source': 'autotrader'
                })

        return listings

    except requests.Timeout:
        print("❌ Request timed out")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def scrape_carfax(make, model, year=None, max_results=20):
    """
    Try Carfax listings - they have an API-like structure
    """

    print(f"Scraping Carfax for: {year or 'any year'} {make} {model}")
    print("-" * 60)

    # Carfax has a cleaner API
    make_slug = make.lower().replace(' ', '-')
    model_slug = model.lower().replace(' ', '-')

    url = f"https://www.carfax.com/Used-{make}-{model}_w0"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for price data in the page
        listings = []

        # Carfax shows prices prominently
        price_elements = soup.find_all(text=re.compile(r'\$[0-9,]+'))

        for price_elem in price_elements[:max_results]:
            price_match = re.search(r'\$([0-9,]+)', price_elem)
            if price_match:
                try:
                    price = int(price_match.group(1).replace(',', ''))
                    if 5000 < price < 500000:  # Sanity check
                        listings.append({
                            'price': price,
                            'source': 'carfax'
                        })
                except:
                    pass

        return listings[:max_results]

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def get_average_market_price(make, model, year=None):
    """
    Get average market price from multiple sources
    """

    print("\n" + "="*60)
    print(f"Getting REAL market prices for: {year or 'Any'} {make} {model}")
    print("="*60 + "\n")

    all_listings = []

    # Try Autotrader
    print("1. Trying Autotrader...")
    at_listings = scrape_autotrader(make, model, year, max_results=25)
    all_listings.extend(at_listings)
    print(f"   Found {len(at_listings)} listings\n")

    time.sleep(2)  # Be nice

    # Try Carfax
    print("2. Trying Carfax...")
    cf_listings = scrape_carfax(make, model, year, max_results=25)
    all_listings.extend(cf_listings)
    print(f"   Found {len(cf_listings)} listings\n")

    if not all_listings:
        print("❌ No listings found from any source")
        return None

    # Calculate statistics
    prices = [l['price'] for l in all_listings if l.get('price')]

    if not prices:
        print("❌ No prices found")
        return None

    import statistics

    avg_price = statistics.mean(prices)
    median_price = statistics.median(prices)
    min_price = min(prices)
    max_price = max(prices)

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Listings found: {len(prices)}")
    print(f"Average price:  ${avg_price:,.0f}")
    print(f"Median price:   ${median_price:,.0f}")
    print(f"Price range:    ${min_price:,.0f} - ${max_price:,.0f}")
    print("="*60 + "\n")

    # Show sample listings
    print("Sample listings:")
    for i, listing in enumerate(all_listings[:10], 1):
        print(f"  {i}. ${listing['price']:>8,}  {listing.get('mileage', 'N/A'):>10}mi  {listing.get('location', listing.get('source'))}")

    return {
        'average': avg_price,
        'median': median_price,
        'min': min_price,
        'max': max_price,
        'sample_size': len(prices),
        'listings': all_listings
    }


if __name__ == "__main__":
    # Test with BMW M4
    result = get_average_market_price("BMW", "M4", year=2024)

    if result:
        print(f"\n✅ 2024 BMW M4 real market value: ${result['median']:,.0f}")
        print(f"   (Average: ${result['average']:,.0f}, based on {result['sample_size']} listings)")

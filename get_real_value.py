"""
Get REAL vehicle values using multiple methods

Methods (in order of accuracy):
1. NADA Guides API (unofficial but works)
2. Edmunds data extraction
3. Manual Google search price aggregation
4. Fallback to our improved depreciation model
"""

import requests
from bs4 import BeautifulSoup
import re
import json


def get_value_from_search(make, model, year):
    """
    Get value by scraping Google Shopping results

    When you search "2024 BMW M4 price", Google shows actual listings
    with real prices from dealers.
    """

    print(f"\n🔍 Searching Google for: {year} {make} {model} for sale")
    print("-" * 60)

    # Google search for car listings
    query = f"{year} {make} {model} for sale price"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=shop"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find price elements
            prices = []

            # Google Shopping shows prices in specific divs
            price_texts = soup.find_all(string=re.compile(r'\$[0-9,]+'))

            for price_text in price_texts:
                match = re.search(r'\$([0-9,]+)', price_text)
                if match:
                    try:
                        price = int(match.group(1).replace(',', ''))
                        # Filter out obviously wrong prices
                        if 10000 < price < 500000:
                            prices.append(price)
                    except:
                        pass

            if prices:
                # Remove outliers (top/bottom 10%)
                prices_sorted = sorted(prices)
                trimmed = prices_sorted[len(prices)//10:-len(prices)//10] if len(prices) > 10 else prices_sorted

                if trimmed:
                    avg = sum(trimmed) / len(trimmed)
                    print(f"✅ Found {len(trimmed)} prices from Google Shopping")
                    print(f"   Average: ${avg:,.0f}")
                    print(f"   Range: ${min(trimmed):,.0f} - ${max(trimmed):,.0f}")
                    return avg

    except Exception as e:
        print(f"❌ Google search failed: {e}")

    return None


def get_edmunds_estimate(make, model, year):
    """
    Get Edmunds TMV (True Market Value) estimate

    Edmunds has good data and is easier to access
    """

    print(f"\n📊 Checking Edmunds for: {year} {make} {model}")
    print("-" * 60)

    # Edmunds URL structure
    make_slug = make.lower().replace(' ', '-')
    model_slug = model.lower().replace(' ', '-')

    url = f"https://www.edmunds.com/{make_slug}/{model_slug}/{year}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for price data
            # Edmunds shows MSRP and typical prices
            prices = []

            # Find all price mentions
            price_texts = soup.find_all(string=re.compile(r'\$[0-9,]+'))

            for price_text in price_texts:
                match = re.search(r'\$([0-9,]+)', price_text)
                if match:
                    try:
                        price = int(match.group(1).replace(',', ''))
                        if 10000 < price < 500000:
                            prices.append(price)
                    except:
                        pass

            if prices:
                # Use median to avoid outliers
                import statistics
                median = statistics.median(prices)
                print(f"✅ Found pricing data")
                print(f"   Estimated value: ${median:,.0f}")
                return median

    except Exception as e:
        print(f"❌ Edmunds lookup failed: {e}")

    return None


def get_manual_estimate(make, model, year):
    """
    Manual lookup - prompt user to input value from KBB/Edmunds

    Sometimes the fastest way is just to look it up manually!
    """

    print(f"\n🔎 Manual Lookup Required")
    print("-" * 60)
    print(f"Vehicle: {year} {make} {model}")
    print()
    print("Please look up the value on:")
    print("  • KBB: https://www.kbb.com/")
    print("  • Edmunds: https://www.edmunds.com/")
    print("  • NADA: https://www.nadaguides.com/")
    print()

    try:
        value_input = input("Enter the average market value (or press Enter to skip): $")
        if value_input.strip():
            value = int(value_input.replace(',', '').replace('$', ''))
            return value
    except:
        pass

    return None


def get_accurate_value(make, model, year, interactive=True):
    """
    Get most accurate value possible using multiple methods
    """

    print("\n" + "="*60)
    print(f"GETTING ACCURATE VALUE: {year} {make} {model}")
    print("="*60)

    # Try methods in order of accuracy
    value = None

    # Method 1: Google Shopping (actual dealer prices)
    value = get_value_from_search(make, model, year)

    if not value:
        # Method 2: Edmunds
        value = get_edmunds_estimate(make, model, year)

    if not value and interactive:
        # Method 3: Manual lookup
        value = get_manual_estimate(make, model, year)

    if not value:
        # Method 4: Our improved depreciation model
        print(f"\n📉 Using improved depreciation model (fallback)")
        print("-" * 60)

        from backend.app.accurate_depreciation import calculate_accurate_value
        value, metadata = calculate_accurate_value(make, model, year)

        print(f"   Estimated value: ${value:,.0f}")
        print(f"   Based on: ${metadata['original_msrp']:,.0f} MSRP")
        print(f"   Confidence: {metadata['confidence']}")

    # Final result
    print("\n" + "="*60)
    if value:
        print(f"✅ FINAL VALUE: ${value:,.0f}")
    else:
        print("❌ Could not determine value")
    print("="*60 + "\n")

    return value


if __name__ == "__main__":
    # Test with BMW M4
    value = get_accurate_value("BMW", "M4", 2024, interactive=True)

    if value:
        print(f"\n🎯 2024 BMW M4 accurate value: ${value:,.0f}")

        # Compare to depreciation model
        from backend.app.accurate_depreciation import calculate_accurate_value
        dep_value, _ = calculate_accurate_value("BMW", "M4", 2024, mileage=5000)

        diff = value - dep_value
        diff_pct = (diff / value) * 100

        print(f"\nComparison:")
        print(f"  Real market value:       ${value:,.0f}")
        print(f"  Depreciation model:      ${dep_value:,.0f}")
        print(f"  Difference:              ${diff:+,.0f} ({diff_pct:+.1f}%)")

        if abs(diff_pct) > 15:
            print(f"\n⚠️  Depreciation model is {abs(diff_pct):.0f}% off!")
            print(f"    Real scraping would give much better accuracy.")

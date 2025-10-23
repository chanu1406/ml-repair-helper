#!/usr/bin/env python3
"""
Demo script to test web scraping (without saving to DB)
"""

import logging

logging.basicConfig(level=logging.INFO)

print("\n" + "="*60)
print("WEB SCRAPER TEST (Demo Mode)")
print("="*60)
print("\nThis will attempt to scrape a few listings from Cars.com")
print("Note: Website selectors may need updating if this fails\n")

from backend.app.scrapers import CarsComScraper

# Test scraping
print("Testing Cars.com scraper...")
print("Target: 2020 Toyota Camry (max 5 results)")
print("-"*60)

try:
    with CarsComScraper(rate_limit=3.0) as scraper:
        listings = scraper.scrape_listings(
            make="Toyota",
            model="Camry",
            year=2020,
            max_results=5,
            zip_code="10001"
        )

        if listings:
            print(f"\n✓ Found {len(listings)} listings!")
            print("\nSample listing:")
            if listings[0]:
                for key, value in listings[0].items():
                    if key != '_raw_data':
                        print(f"  {key}: {value}")
        else:
            print("\n⚠ No listings found")
            print("This likely means the HTML selectors need updating.")
            print("See VEHICLE_VALUATION_README.md for instructions")

        # Show scraper stats
        stats = scraper.get_stats()
        print(f"\nScraper Stats:")
        print(f"  Requests: {stats['requests']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")

except Exception as e:
    print(f"\n✗ Scraper failed: {e}")
    print("\nThis is expected if website structure has changed.")
    print("Update selectors in backend/app/scrapers/cars_com.py")

print("\n" + "="*60)
print("To save listings to database, use:")
print("  python run_scraper.py --make Toyota --model Camry")
print("="*60 + "\n")

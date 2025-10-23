"""
Cars.com scraper using Playwright (headless browser)

This bypasses bot detection by acting like a real browser.
Much more reliable than requests + BeautifulSoup.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
import re

logger = logging.getLogger(__name__)


class CarsComPlaywrightScraper:
    """Scrape Cars.com using Playwright for reliability"""

    def __init__(self):
        self.base_url = "https://www.cars.com"
        self.stats = {
            "requests_made": 0,
            "listings_found": 0,
            "errors": 0
        }

    async def scrape_listings(
        self,
        make: str,
        model: str,
        year: Optional[int] = None,
        max_results: int = 100,
        zip_code: str = "10001",
        radius: int = "all"
    ) -> List[Dict[str, Any]]:
        """
        Scrape Cars.com listings using Playwright

        Args:
            make: Vehicle make (e.g., "BMW")
            model: Vehicle model (e.g., "M4")
            year: Optional year filter
            max_results: Max listings to return
            zip_code: Search location
            radius: Search radius ("all" or miles)

        Returns:
            List of listing dictionaries
        """

        listings = []

        # Build search URL
        make_slug = make.lower()
        model_slug = f"{make.lower()}-{model.lower().replace(' ', '-')}"

        url = f"{self.base_url}/shopping/results/"
        params = f"?stock_type=used&makes[]={make_slug}&models[]={model_slug}&maximum_distance={radius}&zip={zip_code}"

        if year:
            params += f"&year_min={year}&year_max={year}"

        search_url = url + params

        logger.info(f"[Cars.com] Searching: {search_url}")

        async with async_playwright() as p:
            # Launch browser (headless)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()

            try:
                # Navigate to search page
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                self.stats["requests_made"] += 1

                # Wait for listings to load
                try:
                    await page.wait_for_selector('div[class*="vehicle-card"]', timeout=10000)
                except:
                    logger.warning("No vehicle cards found, trying alternative selectors...")

                # Extract listings
                # Cars.com uses different class names, let's try multiple selectors
                listing_elements = await page.query_selector_all('div[class*="vehicle-card"]')

                if not listing_elements:
                    # Try alternative selector
                    listing_elements = await page.query_selector_all('div[data-testid*="vehicle"]')

                if not listing_elements:
                    # Try even more generic
                    listing_elements = await page.query_selector_all('article')

                logger.info(f"Found {len(listing_elements)} potential listings")

                # Extract data from each listing
                for element in listing_elements[:max_results]:
                    try:
                        listing_data = await self._extract_listing_data(element, page)
                        if listing_data:
                            listings.append(listing_data)
                    except Exception as e:
                        logger.error(f"Error extracting listing: {e}")
                        self.stats["errors"] += 1

                self.stats["listings_found"] = len(listings)

            except Exception as e:
                logger.error(f"Error during scraping: {e}")
                self.stats["errors"] += 1

            finally:
                await browser.close()

        logger.info(f"[Cars.com] Scraped {len(listings)} listings")
        return listings

    async def _extract_listing_data(self, element, page) -> Optional[Dict[str, Any]]:
        """Extract data from a single listing element"""

        data = {
            "source": "cars.com",
            "scraped_at": None  # Will be set when saving to DB
        }

        # Get all text content
        text_content = await element.inner_text()

        # Price - look for $XX,XXX pattern
        price_match = re.search(r'\$([0-9,]+)', text_content)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            try:
                data["price"] = float(price_str)
            except:
                pass

        # Mileage - look for XXX,XXX mi pattern
        mileage_match = re.search(r'([0-9,]+)\s*mi', text_content, re.IGNORECASE)
        if mileage_match:
            mileage_str = mileage_match.group(1).replace(',', '')
            try:
                data["mileage"] = int(mileage_str)
            except:
                pass

        # Vehicle title - usually first heading
        try:
            title_elem = await element.query_selector('h2, h3, [class*="title"]')
            if title_elem:
                data["title"] = await title_elem.inner_text()
        except:
            pass

        # Link
        try:
            link_elem = await element.query_selector('a[href*="/vehicledetail/"]')
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href:
                    if href.startswith('http'):
                        data["listing_url"] = href
                    else:
                        data["listing_url"] = self.base_url + href
        except:
            pass

        # Location - look for City, ST pattern
        location_match = re.search(r'([A-Z][a-z]+),\s*([A-Z]{2})', text_content)
        if location_match:
            data["city"] = location_match.group(1)
            data["state"] = location_match.group(2)

        # Only return if we got at least a price
        return data if data.get("price") else None

    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics"""
        return self.stats


# Synchronous wrapper for easy use
def scrape_cars_com(
    make: str,
    model: str,
    year: Optional[int] = None,
    max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for Cars.com scraping

    Args:
        make: Vehicle make
        model: Vehicle model
        year: Optional year
        max_results: Max results

    Returns:
        List of listings
    """

    scraper = CarsComPlaywrightScraper()
    return asyncio.run(scraper.scrape_listings(
        make=make,
        model=model,
        year=year,
        max_results=max_results
    ))


if __name__ == "__main__":
    # Test scraper
    print("Testing Cars.com Playwright scraper...")
    print("Searching for: 2024 BMW M4")
    print("-" * 50)

    listings = scrape_cars_com("BMW", "M4", year=2024, max_results=10)

    print(f"\nFound {len(listings)} listings:\n")

    for i, listing in enumerate(listings, 1):
        print(f"{i}. {listing.get('title', 'N/A')}")
        print(f"   Price: ${listing.get('price', 0):,.0f}")
        print(f"   Mileage: {listing.get('mileage', 'N/A'):,} mi")
        print(f"   Location: {listing.get('city', 'N/A')}, {listing.get('state', 'N/A')}")
        print(f"   URL: {listing.get('listing_url', 'N/A')[:60]}...")
        print()

    if listings:
        avg_price = sum(l['price'] for l in listings if l.get('price')) / len([l for l in listings if l.get('price')])
        print(f"Average price: ${avg_price:,.0f}")

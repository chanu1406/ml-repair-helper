"""
Cars.com scraper for vehicle listings

Note: This is a basic implementation. Cars.com may use JavaScript rendering
and anti-bot measures. For production, you may need Selenium/Playwright.
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from backend.app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CarsComScraper(BaseScraper):
    """Scraper for Cars.com vehicle listings"""

    def __init__(self, rate_limit: float = 2.0):
        super().__init__(
            name="Cars.com",
            base_url="https://www.cars.com",
            rate_limit=rate_limit
        )

    def scrape_listings(
        self,
        make: str,
        model: str,
        year: Optional[int] = None,
        max_results: int = 100,
        zip_code: str = "10001",  # Default to NYC
        radius: int = 500,  # miles
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape Cars.com for vehicle listings

        Args:
            make: Vehicle make
            model: Vehicle model
            year: Optional year
            max_results: Maximum listings to return
            zip_code: Search location ZIP code
            radius: Search radius in miles
            **kwargs: Additional parameters

        Returns:
            List of listing dictionaries
        """
        logger.info(f"[Cars.com] Scraping {year or 'any year'} {make} {model}")

        all_listings = []
        page = 1
        max_pages = (max_results // 20) + 1  # ~20 results per page

        while len(all_listings) < max_results and page <= max_pages:
            try:
                # Build search URL
                url = self._build_search_url(
                    make=make,
                    model=model,
                    year=year,
                    zip_code=zip_code,
                    radius=radius,
                    page=page
                )

                # Make request
                response = self._make_request(url)
                soup = self._parse_html(response.text)

                # Extract listings from page
                listings = self._extract_listings_from_page(soup)

                if not listings:
                    logger.info(f"[Cars.com] No more listings found on page {page}")
                    break

                all_listings.extend(listings)
                logger.info(f"[Cars.com] Page {page}: Found {len(listings)} listings (total: {len(all_listings)})")

                page += 1

            except Exception as e:
                logger.error(f"[Cars.com] Error scraping page {page}: {e}")
                break

        logger.info(f"[Cars.com] Scraping complete: {len(all_listings)} listings")
        return all_listings[:max_results]

    def _build_search_url(
        self,
        make: str,
        model: str,
        year: Optional[int],
        zip_code: str,
        radius: int,
        page: int
    ) -> str:
        """Build Cars.com search URL"""

        # Cars.com URL structure (this may change)
        # Example: https://www.cars.com/shopping/results/?makes[]=toyota&models[]=toyota-camry&page=1

        params = {
            "stock_type": "used",
            "makes[]": make.lower(),
            "models[]": f"{make.lower()}-{model.lower().replace(' ', '_')}",
            "list_price_max": "",
            "maximum_distance": radius,
            "zip": zip_code,
            "page": page,
            "page_size": 20,
            "sort": "best_match_desc"
        }

        if year:
            params["year_min"] = year
            params["year_max"] = year

        # Note: This URL structure is simplified and may need adjustment
        query_string = urlencode(params, doseq=True)
        return f"{self.base_url}/shopping/results/?{query_string}"

    def _extract_listings_from_page(self, soup) -> List[Dict[str, Any]]:
        """
        Extract all listings from a search results page

        Note: This is a template implementation. Cars.com's actual HTML structure
        will require inspection and adjustment.
        """
        listings = []

        # Look for vehicle cards/listings
        # These selectors are examples and need to be updated based on actual site structure
        listing_elements = soup.find_all("div", class_="vehicle-card") or \
                          soup.find_all("div", {"data-testid": "listing"}) or \
                          soup.find_all("article")

        if not listing_elements:
            logger.warning("[Cars.com] No listing elements found - selectors may need updating")
            return listings

        for element in listing_elements:
            listing_data = self.extract_listing_data(element)
            if listing_data and self.validate_listing(listing_data):
                listings.append(listing_data)

        return listings

    def extract_listing_data(self, listing_element) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single listing element

        Note: This is a template. Actual implementation requires
        inspecting Cars.com's HTML structure.
        """
        try:
            data = {
                "source": "cars.com",
                "scraped_at": None  # Will be set when saving to DB
            }

            # Price - example selectors
            price_elem = (
                listing_element.find("span", class_="primary-price") or
                listing_element.find("span", {"data-testid": "price"}) or
                listing_element.find(text=lambda t: t and "$" in str(t))
            )
            if price_elem:
                data["price"] = self.clean_price(price_elem.get_text(strip=True))

            # Mileage - example selectors
            mileage_elem = (
                listing_element.find("div", class_="mileage") or
                listing_element.find(text=lambda t: t and "miles" in str(t).lower())
            )
            if mileage_elem:
                data["mileage"] = self.clean_mileage(mileage_elem.get_text(strip=True))

            # Vehicle title/name
            title_elem = (
                listing_element.find("h2") or
                listing_element.find("h3") or
                listing_element.find("div", class_="title")
            )
            if title_elem:
                data["title"] = title_elem.get_text(strip=True)

            # Listing URL
            link_elem = listing_element.find("a", href=True)
            if link_elem:
                href = link_elem["href"]
                data["listing_url"] = href if href.startswith("http") else f"{self.base_url}{href}"

            # Location
            location_elem = listing_element.find("div", class_="dealer-location")
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                # Parse "City, ST" format
                if "," in location_text:
                    parts = location_text.split(",")
                    data["city"] = parts[0].strip()
                    if len(parts) > 1:
                        data["state"] = parts[1].strip()[:2]

            # VIN (if available)
            vin_elem = listing_element.find("span", class_="vin")
            if vin_elem:
                data["vin"] = vin_elem.get_text(strip=True)

            # Only return if we got at least a price
            return data if data.get("price") else None

        except Exception as e:
            logger.error(f"[Cars.com] Error extracting listing: {e}")
            return None


# Utility function
def scrape_cars_com(make: str, model: str, year: Optional[int] = None, max_results: int = 100):
    """
    Convenience function to scrape Cars.com

    Args:
        make: Vehicle make
        model: Vehicle model
        year: Optional year
        max_results: Max results to return

    Returns:
        List of listings
    """
    with CarsComScraper() as scraper:
        return scraper.scrape_listings(
            make=make,
            model=model,
            year=year,
            max_results=max_results
        )

"""
Autotrader scraper for vehicle listings
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from backend.app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AutotraderScraper(BaseScraper):
    """Scraper for Autotrader vehicle listings"""

    def __init__(self, rate_limit: float = 2.0):
        super().__init__(
            name="Autotrader",
            base_url="https://www.autotrader.com",
            rate_limit=rate_limit
        )

    def scrape_listings(
        self,
        make: str,
        model: str,
        year: Optional[int] = None,
        max_results: int = 100,
        zip_code: str = "10001",
        radius: int = 500,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape Autotrader for vehicle listings
        """
        logger.info(f"[Autotrader] Scraping {year or 'any year'} {make} {model}")

        all_listings = []
        first_record = 0
        records_per_page = 25

        while len(all_listings) < max_results:
            try:
                url = self._build_search_url(
                    make=make,
                    model=model,
                    year=year,
                    zip_code=zip_code,
                    radius=radius,
                    first_record=first_record
                )

                response = self._make_request(url)
                soup = self._parse_html(response.text)

                listings = self._extract_listings_from_page(soup)

                if not listings:
                    logger.info(f"[Autotrader] No more listings found")
                    break

                all_listings.extend(listings)
                logger.info(f"[Autotrader] Found {len(listings)} listings (total: {len(all_listings)})")

                first_record += records_per_page

            except Exception as e:
                logger.error(f"[Autotrader] Error scraping: {e}")
                break

        logger.info(f"[Autotrader] Scraping complete: {len(all_listings)} listings")
        return all_listings[:max_results]

    def _build_search_url(
        self,
        make: str,
        model: str,
        year: Optional[int],
        zip_code: str,
        radius: int,
        first_record: int
    ) -> str:
        """Build Autotrader search URL"""

        params = {
            "makeCodeList": make.upper(),
            "modelCodeList": model.upper().replace(" ", ""),
            "zip": zip_code,
            "searchRadius": radius,
            "firstRecord": first_record,
            "numRecords": 25,
            "sortBy": "relevance"
        }

        if year:
            params["startYear"] = year
            params["endYear"] = year

        query_string = urlencode(params)
        return f"{self.base_url}/cars-for-sale/all-cars?{query_string}"

    def _extract_listings_from_page(self, soup) -> List[Dict[str, Any]]:
        """Extract listings from search results page"""
        listings = []

        # Template selectors - need to be updated based on actual site
        listing_elements = soup.find_all("div", {"data-cmp": "inventoryListing"}) or \
                          soup.find_all("div", class_="inventory-listing")

        for element in listing_elements:
            listing_data = self.extract_listing_data(element)
            if listing_data and self.validate_listing(listing_data):
                listings.append(listing_data)

        return listings

    def extract_listing_data(self, listing_element) -> Optional[Dict[str, Any]]:
        """Extract data from a single listing"""
        try:
            data = {"source": "autotrader"}

            # Price
            price_elem = listing_element.find("span", class_="first-price")
            if price_elem:
                data["price"] = self.clean_price(price_elem.get_text(strip=True))

            # Mileage
            mileage_elem = listing_element.find("span", class_="mileage")
            if mileage_elem:
                data["mileage"] = self.clean_mileage(mileage_elem.get_text(strip=True))

            # Title
            title_elem = listing_element.find("h3") or listing_element.find("h2")
            if title_elem:
                data["title"] = title_elem.get_text(strip=True)

            # URL
            link_elem = listing_element.find("a", href=True)
            if link_elem:
                href = link_elem["href"]
                data["listing_url"] = href if href.startswith("http") else f"{self.base_url}{href}"

            # Location
            location_elem = listing_element.find("div", class_="dealer-location")
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                if "," in location_text:
                    parts = location_text.split(",")
                    data["city"] = parts[0].strip()
                    if len(parts) > 1:
                        data["state"] = parts[1].strip()[:2]

            return data if data.get("price") else None

        except Exception as e:
            logger.error(f"[Autotrader] Error extracting listing: {e}")
            return None

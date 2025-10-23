"""
CarGurus scraper for vehicle listings
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from backend.app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CarGurusScraper(BaseScraper):
    """Scraper for CarGurus vehicle listings"""

    def __init__(self, rate_limit: float = 2.0):
        super().__init__(
            name="CarGurus",
            base_url="https://www.cargurus.com",
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
        Scrape CarGurus for vehicle listings
        """
        logger.info(f"[CarGurus] Scraping {year or 'any year'} {make} {model}")

        all_listings = []
        page = 1

        while len(all_listings) < max_results:
            try:
                url = self._build_search_url(
                    make=make,
                    model=model,
                    year=year,
                    zip_code=zip_code,
                    radius=radius,
                    page=page
                )

                response = self._make_request(url)
                soup = self._parse_html(response.text)

                listings = self._extract_listings_from_page(soup)

                if not listings:
                    logger.info(f"[CarGurus] No more listings found on page {page}")
                    break

                all_listings.extend(listings)
                logger.info(f"[CarGurus] Page {page}: Found {len(listings)} listings (total: {len(all_listings)})")

                page += 1

            except Exception as e:
                logger.error(f"[CarGurus] Error scraping page {page}: {e}")
                break

        logger.info(f"[CarGurus] Scraping complete: {len(all_listings)} listings")
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
        """Build CarGurus search URL"""

        # CarGurus URL format
        make_model = f"{make}-{model}".replace(" ", "-").lower()

        params = {
            "zip": zip_code,
            "distance": radius,
            "page": page
        }

        if year:
            params["startYear"] = year
            params["endYear"] = year

        query_string = urlencode(params)
        return f"{self.base_url}/Cars/{make_model}?{query_string}"

    def _extract_listings_from_page(self, soup) -> List[Dict[str, Any]]:
        """Extract listings from search results page"""
        listings = []

        # Template selectors - need updating based on actual CarGurus structure
        listing_elements = soup.find_all("div", class_="listing-row") or \
                          soup.find_all("div", {"data-cg-ft": "srp-listing-blade"})

        for element in listing_elements:
            listing_data = self.extract_listing_data(element)
            if listing_data and self.validate_listing(listing_data):
                listings.append(listing_data)

        return listings

    def extract_listing_data(self, listing_element) -> Optional[Dict[str, Any]]:
        """Extract data from a single listing"""
        try:
            data = {"source": "cargurus"}

            # Price
            price_elem = listing_element.find("span", class_="price") or \
                        listing_element.find("h4", class_="price-section")
            if price_elem:
                data["price"] = self.clean_price(price_elem.get_text(strip=True))

            # Mileage
            mileage_elem = listing_element.find(text=lambda t: t and "miles" in str(t).lower())
            if mileage_elem:
                data["mileage"] = self.clean_mileage(mileage_elem.strip())

            # Title
            title_elem = listing_element.find("h4") or listing_element.find("h3")
            if title_elem:
                data["title"] = title_elem.get_text(strip=True)

            # URL
            link_elem = listing_element.find("a", href=True)
            if link_elem:
                href = link_elem["href"]
                data["listing_url"] = href if href.startswith("http") else f"{self.base_url}{href}"

            # Deal rating (unique to CarGurus)
            deal_elem = listing_element.find("span", class_="deal-rating")
            if deal_elem:
                data["deal_rating"] = deal_elem.get_text(strip=True)

            # Location
            location_elem = listing_element.find("p", class_="dealer-location")
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                if "," in location_text:
                    parts = location_text.split(",")
                    data["city"] = parts[0].strip()
                    if len(parts) > 1:
                        data["state"] = parts[1].strip()[:2]

            return data if data.get("price") else None

        except Exception as e:
            logger.error(f"[CarGurus] Error extracting listing: {e}")
            return None

"""
Base scraper class with rate limiting, retries, and error handling
"""

import time
import random
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for web scrapers with built-in rate limiting and error handling
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        rate_limit: float = 2.0,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Args:
            name: Scraper name for logging
            base_url: Base URL of the website
            rate_limit: Minimum seconds between requests (default: 2.0)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
        """
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries

        self.last_request_time = 0
        self.request_count = 0
        self.error_count = 0

        # HTTP client with realistic headers
        self.headers = self._get_headers()
        self.client = httpx.Client(
            headers=self.headers,
            timeout=timeout,
            follow_redirects=True
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get realistic browser headers"""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]

        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            # Add small random jitter to avoid detection
            sleep_time += random.uniform(0, 0.5)
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    def _make_request(self, url: str, params: Optional[Dict] = None) -> httpx.Response:
        """
        Make HTTP request with rate limiting and retry logic

        Args:
            url: URL to fetch
            params: Query parameters

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        self._enforce_rate_limit()

        try:
            logger.info(f"[{self.name}] Fetching: {url}")
            response = self.client.get(url, params=params)
            response.raise_for_status()

            self.request_count += 1
            return response

        except httpx.HTTPError as e:
            self.error_count += 1
            logger.error(f"[{self.name}] Request failed: {url} - {e}")
            raise

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html, 'lxml')

    @abstractmethod
    def scrape_listings(
        self,
        make: str,
        model: str,
        year: Optional[int] = None,
        max_results: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape vehicle listings

        Args:
            make: Vehicle make (e.g., "Toyota")
            model: Vehicle model (e.g., "Camry")
            year: Optional model year
            max_results: Maximum number of results to return
            **kwargs: Additional scraper-specific parameters

        Returns:
            List of listing dictionaries

        Must be implemented by subclasses
        """
        raise NotImplementedError

    @abstractmethod
    def extract_listing_data(self, listing_element) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single listing element

        Args:
            listing_element: BeautifulSoup element containing listing

        Returns:
            Dictionary with listing data or None if extraction failed

        Must be implemented by subclasses
        """
        raise NotImplementedError

    def validate_listing(self, listing: Dict[str, Any]) -> bool:
        """
        Validate that a listing has required fields

        Args:
            listing: Listing dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["price", "source"]
        return all(field in listing and listing[field] is not None for field in required_fields)

    def clean_price(self, price_str: str) -> Optional[float]:
        """
        Clean and parse price string to float

        Args:
            price_str: Price string (e.g., "$25,000", "25000")

        Returns:
            Float price or None if parsing failed
        """
        if not price_str:
            return None

        try:
            # Remove currency symbols, commas, spaces
            cleaned = price_str.replace("$", "").replace(",", "").replace(" ", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            logger.warning(f"[{self.name}] Failed to parse price: {price_str}")
            return None

    def clean_mileage(self, mileage_str: str) -> Optional[int]:
        """
        Clean and parse mileage string to int

        Args:
            mileage_str: Mileage string (e.g., "50,000 miles", "50000")

        Returns:
            Integer mileage or None if parsing failed
        """
        if not mileage_str:
            return None

        try:
            # Remove commas, "miles", "km", spaces
            cleaned = (
                mileage_str.lower()
                .replace(",", "")
                .replace("miles", "")
                .replace("mi", "")
                .replace("km", "")
                .replace(" ", "")
                .strip()
            )
            return int(float(cleaned))
        except (ValueError, AttributeError):
            logger.warning(f"[{self.name}] Failed to parse mileage: {mileage_str}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics"""
        return {
            "name": self.name,
            "requests": self.request_count,
            "errors": self.error_count,
            "success_rate": (
                (self.request_count - self.error_count) / self.request_count
                if self.request_count > 0
                else 0
            )
        }

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info(f"[{self.name}] Closed - Stats: {self.get_stats()}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Destructor"""
        self.close()

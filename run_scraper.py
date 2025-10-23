#!/usr/bin/env python3
"""
Utility script to run vehicle listing scrapers and populate the database

Usage:
    python run_scraper.py --make Toyota --model Camry --year 2020 --max-results 50
    python run_scraper.py --make BMW --model "3 Series" --sources cars.com,autotrader
    python run_scraper.py --config scraper_config.json
"""

import argparse
import logging
import sys
from typing import List

from backend.app.scrapers import CarsComScraper, AutotraderScraper, CarGurusScraper
from backend.app.pipeline.data_processor import process_and_save_listings
from backend.app.database.session import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_scraper(
    make: str,
    model: str,
    year: int = None,
    max_results: int = 100,
    sources: List[str] = None,
    zip_code: str = "10001"
):
    """
    Run scrapers and save results to database

    Args:
        make: Vehicle make
        model: Vehicle model
        year: Optional vehicle year
        max_results: Max results per source
        sources: List of sources to scrape
        zip_code: Search location ZIP
    """

    if sources is None:
        sources = ["cars.com", "autotrader", "cargurus"]

    logger.info(f"Starting scraping job: {year or 'any year'} {make} {model}")
    logger.info(f"Sources: {', '.join(sources)}")
    logger.info(f"Max results per source: {max_results}")

    all_listings = []

    # Run scrapers
    if "cars.com" in sources:
        logger.info("Scraping Cars.com...")
        try:
            with CarsComScraper() as scraper:
                listings = scraper.scrape_listings(
                    make=make,
                    model=model,
                    year=year,
                    max_results=max_results,
                    zip_code=zip_code
                )
                all_listings.extend(listings)
                logger.info(f"Cars.com: Found {len(listings)} listings")
        except Exception as e:
            logger.error(f"Cars.com scraping failed: {e}")

    if "autotrader" in sources:
        logger.info("Scraping Autotrader...")
        try:
            with AutotraderScraper() as scraper:
                listings = scraper.scrape_listings(
                    make=make,
                    model=model,
                    year=year,
                    max_results=max_results,
                    zip_code=zip_code
                )
                all_listings.extend(listings)
                logger.info(f"Autotrader: Found {len(listings)} listings")
        except Exception as e:
            logger.error(f"Autotrader scraping failed: {e}")

    if "cargurus" in sources:
        logger.info("Scraping CarGurus...")
        try:
            with CarGurusScraper() as scraper:
                listings = scraper.scrape_listings(
                    make=make,
                    model=model,
                    year=year,
                    max_results=max_results,
                    zip_code=zip_code
                )
                all_listings.extend(listings)
                logger.info(f"CarGurus: Found {len(listings)} listings")
        except Exception as e:
            logger.error(f"CarGurus scraping failed: {e}")

    # Process and save to database
    if all_listings:
        logger.info(f"Processing {len(all_listings)} total listings...")
        stats = process_and_save_listings(all_listings)
        logger.info(f"Processing complete: {stats}")
        return stats
    else:
        logger.warning("No listings found!")
        return {"total": 0, "saved": 0, "failed": 0}


def main():
    parser = argparse.ArgumentParser(
        description="Run vehicle listing scrapers"
    )
    parser.add_argument(
        "--make",
        required=True,
        help="Vehicle make (e.g., Toyota, BMW)"
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Vehicle model (e.g., Camry, '3 Series')"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Vehicle year (optional)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum results per source (default: 100)"
    )
    parser.add_argument(
        "--sources",
        default="cars.com,autotrader,cargurus",
        help="Comma-separated list of sources (default: all)"
    )
    parser.add_argument(
        "--zip",
        default="10001",
        help="Search location ZIP code (default: 10001)"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database before scraping"
    )

    args = parser.parse_args()

    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database...")
        init_db()

    # Parse sources
    sources = [s.strip() for s in args.sources.split(",")]

    # Run scraper
    try:
        stats = run_scraper(
            make=args.make,
            model=args.model,
            year=args.year,
            max_results=args.max_results,
            sources=sources,
            zip_code=args.zip
        )

        logger.info("=" * 60)
        logger.info("SCRAPING JOB COMPLETE")
        logger.info(f"Total listings found: {stats['total']}")
        logger.info(f"Successfully saved: {stats['saved']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

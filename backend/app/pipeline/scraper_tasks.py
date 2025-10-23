"""
Scraper task orchestration for scheduled and manual scraping jobs

This module provides task functions for running scrapers and updating valuations.
Can be used with Celery for scheduled tasks or called directly.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.database.session import get_session
from backend.app.database.models import ScraperLog, VehicleValuation
from backend.app.scrapers.cars_com import CarsComScraper
from backend.app.scrapers.autotrader import AutotraderScraper
from backend.app.scrapers.cargurus import CarGurusScraper
from backend.app.pipeline.data_processor import process_and_save_listings

logger = logging.getLogger(__name__)


def run_scraper_job(
    make: str,
    model: str,
    year: Optional[int] = None,
    max_results: int = 100,
    sources: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run a scraping job across multiple sources

    Args:
        make: Vehicle make (e.g., "Toyota")
        model: Vehicle model (e.g., "Camry")
        year: Optional year filter
        max_results: Maximum results per source
        sources: List of sources to scrape (default: all)

    Returns:
        Dict with job statistics
    """

    if sources is None:
        sources = ["cars_com", "autotrader", "cargurus"]

    job_start = datetime.utcnow()
    all_listings = []
    results = {
        "make": make,
        "model": model,
        "year": year,
        "total_listings": 0,
        "sources": {},
        "errors": []
    }

    logger.info(f"Starting scraper job: {year or 'any'} {make} {model}")

    # Run each scraper
    for source in sources:
        try:
            logger.info(f"Scraping {source}...")

            if source == "cars_com":
                scraper = CarsComScraper()
            elif source == "autotrader":
                scraper = AutotraderScraper()
            elif source == "cargurus":
                scraper = CarGurusScraper()
            else:
                logger.warning(f"Unknown source: {source}")
                continue

            # Run scraper
            listings = scraper.search_vehicles(
                make=make,
                model=model,
                year=year,
                max_results=max_results
            )

            # Get stats
            stats = scraper.get_stats()

            all_listings.extend(listings)

            results["sources"][source] = {
                "listings_found": len(listings),
                "requests_made": stats.get("requests_made", 0),
                "errors": stats.get("errors", 0)
            }

            logger.info(f"{source}: Found {len(listings)} listings")

        except Exception as e:
            logger.error(f"Error scraping {source}: {e}")
            results["errors"].append(f"{source}: {str(e)}")

    # Process and save all listings
    try:
        if all_listings:
            saved_count = process_and_save_listings(all_listings)
            results["total_listings"] = len(all_listings)
            results["saved_to_db"] = saved_count
            logger.info(f"Saved {saved_count} listings to database")
        else:
            results["saved_to_db"] = 0
            logger.warning("No listings found from any source")
    except Exception as e:
        logger.error(f"Error saving listings: {e}")
        results["errors"].append(f"Database save error: {str(e)}")

    # Log job completion
    job_end = datetime.utcnow()
    results["duration_seconds"] = (job_end - job_start).total_seconds()
    results["completed_at"] = job_end.isoformat()

    # Save to scraper_logs table
    _log_scraper_job(results)

    return results


def update_valuations(min_sample_size: int = 5) -> Dict[str, Any]:
    """
    Update vehicle valuations from recent listings

    This aggregates recent listings into valuation statistics
    for each unique VIN or make/model/year combination.

    Args:
        min_sample_size: Minimum number of listings needed to create valuation

    Returns:
        Dict with update statistics
    """

    from sqlalchemy import func
    from backend.app.database.models import VehicleListing

    db = get_session()

    try:
        logger.info("Starting valuation update...")

        # Group listings by VIN and calculate statistics
        valuations_updated = 0
        valuations_created = 0

        # Get all VINs with recent listings
        vins_with_listings = (
            db.query(VehicleListing.vin)
            .filter(VehicleListing.vin.isnot(None))
            .group_by(VehicleListing.vin)
            .having(func.count(VehicleListing.id) >= min_sample_size)
            .all()
        )

        for (vin,) in vins_with_listings:
            # Get all listings for this VIN
            listings = (
                db.query(VehicleListing)
                .filter_by(vin=vin)
                .filter(VehicleListing.price.isnot(None))
                .all()
            )

            if len(listings) < min_sample_size:
                continue

            # Calculate statistics
            import statistics
            prices = [l.price for l in listings]
            mileages = [l.mileage for l in listings if l.mileage]

            avg_price = statistics.mean(prices)
            median_price = statistics.median(prices)
            min_price = min(prices)
            max_price = max(prices)
            std_dev = statistics.stdev(prices) if len(prices) > 1 else 0

            # Estimate retail vs trade-in
            retail_value = statistics.mean(sorted(prices, reverse=True)[:len(prices)//3])
            trade_in_value = avg_price * 0.75

            avg_mileage = statistics.mean(mileages) if mileages else None

            # Check if valuation exists
            valuation = db.query(VehicleValuation).filter_by(vin=vin).first()

            if valuation:
                # Update existing
                valuation.avg_price = avg_price
                valuation.median_price = median_price
                valuation.min_price = min_price
                valuation.max_price = max_price
                valuation.std_dev = std_dev
                valuation.retail_value = retail_value
                valuation.trade_in_value = trade_in_value
                valuation.avg_mileage = avg_mileage
                valuation.sample_size = len(listings)
                valuation.last_updated = datetime.utcnow()
                valuations_updated += 1
            else:
                # Create new
                # Get make/model/year from first listing
                first_listing = listings[0]

                valuation = VehicleValuation(
                    vin=vin,
                    make=first_listing.make,
                    model=first_listing.model,
                    year=first_listing.year,
                    avg_price=avg_price,
                    median_price=median_price,
                    min_price=min_price,
                    max_price=max_price,
                    std_dev=std_dev,
                    retail_value=retail_value,
                    trade_in_value=trade_in_value,
                    avg_mileage=avg_mileage,
                    sample_size=len(listings)
                )
                db.add(valuation)
                valuations_created += 1

        db.commit()

        results = {
            "valuations_updated": valuations_updated,
            "valuations_created": valuations_created,
            "total_valuations": valuations_updated + valuations_created,
            "completed_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Valuation update complete: {results['total_valuations']} valuations processed")

        return results

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating valuations: {e}")
        raise
    finally:
        db.close()


def _log_scraper_job(job_results: Dict[str, Any]) -> None:
    """Log scraper job to database"""

    db = get_session()

    try:
        log_entry = ScraperLog(
            source=", ".join(job_results.get("sources", {}).keys()),
            make=job_results.get("make"),
            model=job_results.get("model"),
            year=job_results.get("year"),
            listings_found=job_results.get("total_listings", 0),
            listings_saved=job_results.get("saved_to_db", 0),
            errors_count=len(job_results.get("errors", [])),
            duration_seconds=job_results.get("duration_seconds", 0),
            completed_at=datetime.utcnow()
        )

        db.add(log_entry)
        db.commit()

    except Exception as e:
        logger.error(f"Error logging scraper job: {e}")
        db.rollback()
    finally:
        db.close()


# Celery task definitions (uncomment when Celery is set up)
#
# from celery import Celery
#
# celery_app = Celery('scraper_tasks', broker='redis://localhost:6379/0')
#
# @celery_app.task
# def scheduled_scrape_popular_vehicles():
#     """Scheduled task to scrape popular vehicle makes/models"""
#     popular_vehicles = [
#         ("Toyota", "Camry"),
#         ("Honda", "Civic"),
#         ("Ford", "F-150"),
#         ("Chevrolet", "Silverado"),
#         ("Toyota", "RAV4"),
#     ]
#
#     for make, model in popular_vehicles:
#         run_scraper_job(make, model, max_results=50)
#
#     # Update valuations after scraping
#     update_valuations()

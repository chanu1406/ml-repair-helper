"""
Data processing pipeline for cleaning, validating, and saving scraped listings
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.models import VehicleSpecification, VehicleListing, VehicleValuation
from backend.app.database.session import get_session
from backend.app.nhtsa_service import get_nhtsa_service

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and validate scraped vehicle listings"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_session()
        self.nhtsa = get_nhtsa_service()

    def process_listing(self, listing_data: Dict[str, Any]) -> Optional[VehicleListing]:
        """
        Process a single listing: validate, enrich with NHTSA data, save to DB

        Args:
            listing_data: Raw listing dictionary from scraper

        Returns:
            VehicleListing object if successful, None otherwise
        """
        try:
            # Extract VIN if available
            vin = listing_data.get("vin")

            # If we have a VIN, decode it and create/update vehicle specification
            if vin and len(vin) == 17:
                spec = self._get_or_create_vehicle_spec(vin)
                if not spec:
                    logger.warning(f"Failed to get vehicle spec for VIN: {vin}")
                    return None
            else:
                # No VIN - we'll need to match by make/model/year later
                vin = None
                spec = None

            # Create listing object
            listing = VehicleListing(
                vin=vin,
                price=listing_data.get("price"),
                original_price=listing_data.get("original_price"),
                mileage=listing_data.get("mileage"),
                condition=listing_data.get("condition", "used"),
                city=listing_data.get("city"),
                state=listing_data.get("state"),
                zip_code=listing_data.get("zip_code"),
                source=listing_data.get("source"),
                listing_url=listing_data.get("listing_url"),
                listing_id=listing_data.get("listing_id"),
                listing_date=listing_data.get("listing_date"),
                scraped_at=datetime.utcnow(),
                dealer_name=listing_data.get("dealer_name"),
                days_on_market=listing_data.get("days_on_market"),
                features=listing_data.get("features")
            )

            # Save to database
            self.db.add(listing)
            self.db.commit()
            self.db.refresh(listing)

            logger.info(f"Saved listing: {listing.id} - ${listing.price:,.0f} from {listing.source}")
            return listing

        except Exception as e:
            logger.error(f"Error processing listing: {e}")
            self.db.rollback()
            return None

    def _get_or_create_vehicle_spec(self, vin: str) -> Optional[VehicleSpecification]:
        """Get existing vehicle spec or create new one from NHTSA"""
        try:
            # Check if already in database
            spec = self.db.query(VehicleSpecification).filter_by(vin=vin).first()
            if spec:
                return spec

            # Decode VIN with NHTSA
            nhtsa_data = self.nhtsa.decode_vin(vin)

            # Create new specification
            spec = VehicleSpecification(
                vin=vin,
                make=nhtsa_data.get("make"),
                model=nhtsa_data.get("model"),
                year=nhtsa_data.get("year"),
                trim=nhtsa_data.get("trim"),
                body_type=nhtsa_data.get("body_type"),
                vehicle_type=nhtsa_data.get("vehicle_type"),
                manufacturer=nhtsa_data.get("manufacturer"),
                engine_cylinders=nhtsa_data.get("engine_cylinders"),
                engine_displacement=nhtsa_data.get("engine_displacement"),
                fuel_type=nhtsa_data.get("fuel_type"),
                transmission=nhtsa_data.get("transmission"),
                drive_type=nhtsa_data.get("drive_type"),
                doors=nhtsa_data.get("doors"),
                plant_city=nhtsa_data.get("plant_city"),
                plant_country=nhtsa_data.get("plant_country"),
                source="NHTSA",
                raw_data=nhtsa_data.get("_raw_data")
            )

            self.db.add(spec)
            self.db.commit()
            self.db.refresh(spec)

            logger.info(f"Created vehicle spec: {spec.year} {spec.make} {spec.model} (VIN: {vin})")
            return spec

        except Exception as e:
            logger.error(f"Error getting/creating vehicle spec for VIN {vin}: {e}")
            self.db.rollback()
            return None

    def process_batch(self, listings: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Process a batch of listings

        Args:
            listings: List of listing dictionaries

        Returns:
            Statistics dictionary
        """
        stats = {
            "total": len(listings),
            "saved": 0,
            "failed": 0
        }

        for listing_data in listings:
            result = self.process_listing(listing_data)
            if result:
                stats["saved"] += 1
            else:
                stats["failed"] += 1

        logger.info(f"Batch processing complete: {stats}")
        return stats

    def remove_duplicates(self, days: int = 30):
        """
        Remove duplicate listings based on URL or listing_id

        Args:
            days: Only check listings from last N days
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Find duplicates by listing_url
        duplicates = (
            self.db.query(VehicleListing.listing_url, func.count(VehicleListing.id))
            .filter(VehicleListing.scraped_at >= cutoff_date)
            .group_by(VehicleListing.listing_url)
            .having(func.count(VehicleListing.id) > 1)
            .all()
        )

        removed = 0
        for url, count in duplicates:
            # Keep the most recent, delete older ones
            listings = (
                self.db.query(VehicleListing)
                .filter_by(listing_url=url)
                .order_by(VehicleListing.scraped_at.desc())
                .all()
            )

            # Delete all except the first (most recent)
            for listing in listings[1:]:
                self.db.delete(listing)
                removed += 1

        self.db.commit()
        logger.info(f"Removed {removed} duplicate listings")
        return removed

    def clean_old_listings(self, days: int = 90):
        """
        Remove listings older than specified days

        Args:
            days: Keep only listings from last N days
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = (
            self.db.query(VehicleListing)
            .filter(VehicleListing.scraped_at < cutoff_date)
            .delete()
        )

        self.db.commit()
        logger.info(f"Deleted {deleted} old listings (older than {days} days)")
        return deleted


def process_and_save_listings(listings: List[Dict[str, Any]], db: Optional[Session] = None) -> Dict[str, int]:
    """
    Convenience function to process and save listings

    Args:
        listings: List of listing dictionaries
        db: Optional database session

    Returns:
        Statistics dictionary
    """
    processor = DataProcessor(db=db)
    return processor.process_batch(listings)

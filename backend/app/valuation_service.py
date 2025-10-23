"""
Vehicle Valuation Service using real market data from scraped listings
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.models import VehicleSpecification, VehicleListing, VehicleValuation
from backend.app.database.session import get_session
from backend.app.nhtsa_service import get_nhtsa_service
from backend.app.accurate_depreciation import calculate_accurate_value as fallback_valuation

logger = logging.getLogger(__name__)


class ValuationService:
    """
    Vehicle valuation service combining NHTSA data and market listings
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_session()
        self.nhtsa = get_nhtsa_service()

    def get_vehicle_value(
        self,
        vin: Optional[str] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        mileage: Optional[int] = None,
        state: Optional[str] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Get vehicle value estimate using market data

        Args:
            vin: Vehicle VIN (preferred)
            make: Vehicle make (fallback if no VIN)
            model: Vehicle model (fallback if no VIN)
            year: Vehicle year (fallback if no VIN)
            mileage: Current vehicle mileage
            state: State for regional adjustments

        Returns:
            Tuple of (estimated_value, metadata_dict)
        """

        # Strategy 1: Try VIN-based valuation
        if vin and len(vin) == 17:
            result = self._get_value_by_vin(vin, mileage, state)
            if result:
                return result

        # Strategy 2: Try make/model/year valuation
        if make and model and year:
            result = self._get_value_by_make_model_year(make, model, year, mileage, state)
            if result:
                return result

        # Strategy 3: Try web scraping for real market data
        if make and model and year:
            try:
                from get_real_value import get_accurate_value
                logger.info(f"Attempting to scrape real market data for {year} {make} {model}")
                scraped_value = get_accurate_value(make, model, year, interactive=False)

                if scraped_value:
                    logger.info(f"Successfully scraped market value: ${scraped_value:,.0f}")
                    metadata = {
                        "data_source": "web_scraping",
                        "confidence": "high",
                        "make": make,
                        "model": model,
                        "year": year,
                        "method": "edmunds_or_google_shopping"
                    }
                    return scraped_value, metadata
            except Exception as e:
                logger.warning(f"Web scraping failed: {e}")

        # Strategy 4: Final fallback to accurate industry depreciation model
        logger.warning(f"No market data found, using industry depreciation for {year} {make} {model}")
        value, metadata = fallback_valuation(
            make=make or "Toyota",
            model=model or "Camry",
            year=year or 2010,
            mileage=mileage
        )
        metadata["data_source"] = "industry_depreciation"
        metadata["confidence"] = "medium"  # Better than old model!
        return value, metadata

    def _get_value_by_vin(
        self,
        vin: str,
        mileage: Optional[int],
        state: Optional[str]
    ) -> Optional[Tuple[float, Dict[str, Any]]]:
        """Get valuation using exact VIN match"""

        try:
            # Check if we have cached valuation
            valuation = self.db.query(VehicleValuation).filter_by(vin=vin).first()

            # If valuation exists and is recent (< 7 days old), use it
            if valuation and self._is_valuation_fresh(valuation, days=7):
                value = self._adjust_for_mileage_and_region(
                    valuation.avg_price,
                    mileage,
                    valuation.avg_mileage,
                    state
                )

                metadata = {
                    "vin": vin,
                    "data_source": "cached_valuation",
                    "sample_size": valuation.sample_size,
                    "confidence": self._calculate_confidence(valuation),
                    "last_updated": valuation.last_updated.isoformat(),
                    "retail_value": valuation.retail_value,
                    "trade_in_value": valuation.trade_in_value,
                    "avg_mileage": valuation.avg_mileage
                }

                return value, metadata

            # No cached data or stale - try to compute from listings
            listings = self._get_recent_listings(vin=vin)

            if listings and len(listings) >= 3:  # Need at least 3 listings
                return self._calculate_value_from_listings(
                    listings,
                    vin=vin,
                    mileage=mileage,
                    state=state
                )

        except Exception as e:
            logger.error(f"Error getting value by VIN {vin}: {e}")

        return None

    def _get_value_by_make_model_year(
        self,
        make: str,
        model: str,
        year: int,
        mileage: Optional[int],
        state: Optional[str]
    ) -> Optional[Tuple[float, Dict[str, Any]]]:
        """Get valuation using make/model/year match"""

        try:
            # Get all specs matching make/model/year
            specs = (
                self.db.query(VehicleSpecification)
                .filter_by(make=make, model=model, year=year)
                .all()
            )

            if not specs:
                logger.info(f"No specs found for {year} {make} {model}")
                return None

            # Collect all listings for these specs
            all_listings = []
            for spec in specs:
                listings = self._get_recent_listings(vin=spec.vin)
                all_listings.extend(listings)

            if len(all_listings) >= 5:  # Need reasonable sample
                return self._calculate_value_from_listings(
                    all_listings,
                    make=make,
                    model=model,
                    year=year,
                    mileage=mileage,
                    state=state
                )

        except Exception as e:
            logger.error(f"Error getting value by make/model/year: {e}")

        return None

    def _get_recent_listings(
        self,
        vin: Optional[str] = None,
        days: int = 60
    ) -> list:
        """Get recent listings for a VIN"""

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(VehicleListing).filter(
            VehicleListing.scraped_at >= cutoff_date,
            VehicleListing.price.isnot(None)
        )

        if vin:
            query = query.filter_by(vin=vin)

        return query.all()

    def _calculate_value_from_listings(
        self,
        listings: list,
        vin: Optional[str] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        mileage: Optional[int] = None,
        state: Optional[str] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate valuation statistics from listings"""

        import statistics

        prices = [l.price for l in listings if l.price]
        mileages = [l.mileage for l in listings if l.mileage]

        # Calculate statistics
        avg_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        std_dev = statistics.stdev(prices) if len(prices) > 1 else 0

        # Estimate retail vs trade-in
        retail_value = statistics.mean(sorted(prices, reverse=True)[:len(prices)//3])  # Top 1/3
        trade_in_value = avg_price * 0.75  # Rough estimate

        avg_mileage = statistics.mean(mileages) if mileages else None

        # Adjust for mileage and region
        adjusted_value = self._adjust_for_mileage_and_region(
            avg_price,
            mileage,
            avg_mileage,
            state
        )

        # Build metadata
        metadata = {
            "data_source": "market_listings",
            "sample_size": len(listings),
            "avg_price": avg_price,
            "median_price": median_price,
            "min_price": min(prices),
            "max_price": max(prices),
            "std_dev": std_dev,
            "retail_value": retail_value,
            "trade_in_value": trade_in_value,
            "avg_mileage": avg_mileage,
            "confidence": self._calculate_confidence_from_sample(len(listings), std_dev, avg_price),
            "data_age_days": (datetime.utcnow() - min(l.scraped_at for l in listings)).days
        }

        if vin:
            metadata["vin"] = vin
        if make and model and year:
            metadata["make"] = make
            metadata["model"] = model
            metadata["year"] = year

        logger.info(f"Calculated value from {len(listings)} listings: ${adjusted_value:,.0f}")

        return adjusted_value, metadata

    def _adjust_for_mileage_and_region(
        self,
        base_price: float,
        actual_mileage: Optional[int],
        avg_mileage: Optional[int],
        state: Optional[str]
    ) -> float:
        """Adjust price based on mileage and region"""

        adjusted = base_price

        # Mileage adjustment
        if actual_mileage and avg_mileage:
            mileage_diff = actual_mileage - avg_mileage
            # Roughly $0.10 per mile difference
            mileage_adjustment = mileage_diff * -0.10
            adjusted += mileage_adjustment

        # Regional adjustment (from enhanced_valuation.py)
        if state:
            from backend.app.enhanced_valuation import REGIONAL_MULTIPLIERS
            multiplier = REGIONAL_MULTIPLIERS.get(state, 1.0)
            adjusted *= multiplier

        return adjusted

    @staticmethod
    def _is_valuation_fresh(valuation: VehicleValuation, days: int = 7) -> bool:
        """Check if valuation is recent enough"""
        age = datetime.utcnow() - valuation.last_updated
        return age.days < days

    @staticmethod
    def _calculate_confidence(valuation: VehicleValuation) -> str:
        """Calculate confidence level from valuation"""
        if valuation.sample_size >= 20:
            return "high"
        elif valuation.sample_size >= 10:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _calculate_confidence_from_sample(sample_size: int, std_dev: float, avg: float) -> str:
        """Calculate confidence from sample statistics"""
        if sample_size >= 20 and (std_dev / avg) < 0.2:
            return "high"
        elif sample_size >= 10 and (std_dev / avg) < 0.3:
            return "medium"
        else:
            return "low"


# Global instance
_valuation_service = None

def get_valuation_service() -> ValuationService:
    """Get or create valuation service singleton"""
    global _valuation_service
    if _valuation_service is None:
        _valuation_service = ValuationService()
    return _valuation_service


# Convenience functions
def get_vehicle_value(
    vin: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    mileage: Optional[int] = None,
    state: Optional[str] = None
) -> Tuple[float, Dict[str, Any]]:
    """Get vehicle value estimate"""
    service = get_valuation_service()
    return service.get_vehicle_value(
        vin=vin,
        make=make,
        model=model,
        year=year,
        mileage=mileage,
        state=state
    )

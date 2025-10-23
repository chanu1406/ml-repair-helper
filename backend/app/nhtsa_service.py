"""
NHTSA API Service for VIN Decoding and Vehicle Specifications

Free API provided by the National Highway Traffic Safety Administration
API Documentation: https://vpic.nhtsa.dot.gov/api/
"""

import httpx
from typing import Dict, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

NHTSA_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"


class NHTSAService:
    """Service for interacting with NHTSA vPIC API"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def __del__(self):
        """Clean up HTTP client"""
        if hasattr(self, 'client'):
            self.client.close()

    @lru_cache(maxsize=1000)
    def decode_vin(self, vin: str) -> Dict[str, Any]:
        """
        Decode a VIN to get vehicle specifications

        Args:
            vin: 17-character Vehicle Identification Number

        Returns:
            Dictionary with vehicle specifications

        Raises:
            ValueError: If VIN is invalid
            httpx.HTTPError: If API request fails
        """
        if not vin or len(vin) != 17:
            raise ValueError(f"Invalid VIN: must be 17 characters, got {len(vin) if vin else 0}")

        vin = vin.upper().strip()

        try:
            url = f"{NHTSA_BASE_URL}/DecodeVin/{vin}?format=json"
            response = self.client.get(url)
            response.raise_for_status()

            data = response.json()

            if data.get("Count") == 0:
                raise ValueError(f"No vehicle found for VIN: {vin}")

            # Parse results into a clean dictionary
            results = data.get("Results", [])
            parsed = self._parse_decode_results(results)

            logger.info(f"Successfully decoded VIN: {vin}")
            return parsed

        except httpx.HTTPError as e:
            logger.error(f"NHTSA API error for VIN {vin}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error decoding VIN {vin}: {e}")
            raise

    def _parse_decode_results(self, results: list) -> Dict[str, Any]:
        """Parse NHTSA API results into a clean dictionary"""

        # Create a mapping of variable names to values
        data_map = {item["Variable"]: item["Value"] for item in results if item.get("Value")}

        # Extract key fields
        parsed = {
            "vin": data_map.get("VIN"),
            "make": data_map.get("Make"),
            "model": data_map.get("Model"),
            "year": self._safe_int(data_map.get("Model Year")),
            "trim": data_map.get("Trim"),
            "body_type": data_map.get("Body Class"),
            "vehicle_type": data_map.get("Vehicle Type"),
            "manufacturer": data_map.get("Manufacturer Name"),

            # Engine & Drivetrain
            "engine_cylinders": self._safe_int(data_map.get("Engine Number of Cylinders")),
            "engine_displacement": data_map.get("Displacement (L)"),
            "fuel_type": data_map.get("Fuel Type - Primary"),
            "transmission": data_map.get("Transmission Style"),
            "drive_type": data_map.get("Drive Type"),

            # Additional specs
            "doors": self._safe_int(data_map.get("Doors")),
            "plant_city": data_map.get("Plant City"),
            "plant_country": data_map.get("Plant Country"),

            # Safety
            "airbag_locations": data_map.get("Air Bag Loc Front"),
            "abs": data_map.get("ABS"),

            # Categories
            "series": data_map.get("Series"),
            "trim2": data_map.get("Trim2"),

            # Raw data for reference
            "_raw_data": data_map
        }

        # Remove None values
        return {k: v for k, v in parsed.items() if v is not None}

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """Safely convert value to int"""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def get_models_for_make(self, make: str) -> list:
        """
        Get all models for a specific make

        Args:
            make: Vehicle manufacturer name (e.g., "Toyota", "BMW")

        Returns:
            List of model names
        """
        try:
            url = f"{NHTSA_BASE_URL}/GetModelsForMake/{make}?format=json"
            response = self.client.get(url)
            response.raise_for_status()

            data = response.json()
            results = data.get("Results", [])

            models = [item["Model_Name"] for item in results if item.get("Model_Name")]
            logger.info(f"Found {len(models)} models for {make}")
            return models

        except httpx.HTTPError as e:
            logger.error(f"NHTSA API error getting models for {make}: {e}")
            raise

    def get_makes_for_year(self, year: int) -> list:
        """
        Get all makes available for a specific year

        Args:
            year: Model year (e.g., 2024)

        Returns:
            List of make names
        """
        try:
            url = f"{NHTSA_BASE_URL}/GetMakesForVehicleType/car?year={year}&format=json"
            response = self.client.get(url)
            response.raise_for_status()

            data = response.json()
            results = data.get("Results", [])

            makes = [item["MakeName"] for item in results if item.get("MakeName")]
            logger.info(f"Found {len(makes)} makes for year {year}")
            return makes

        except httpx.HTTPError as e:
            logger.error(f"NHTSA API error getting makes for year {year}: {e}")
            raise


# Global instance
_nhtsa_service = None

def get_nhtsa_service() -> NHTSAService:
    """Get or create NHTSA service singleton"""
    global _nhtsa_service
    if _nhtsa_service is None:
        _nhtsa_service = NHTSAService()
    return _nhtsa_service


# Convenience functions
def decode_vin(vin: str) -> Dict[str, Any]:
    """Decode a VIN using NHTSA API"""
    service = get_nhtsa_service()
    return service.decode_vin(vin)


def get_vehicle_info(make: str, model: str, year: int) -> Dict[str, Any]:
    """
    Get vehicle information by make, model, year
    Note: This is less accurate than VIN decoding as it doesn't get trim-specific data
    """
    return {
        "make": make,
        "model": model,
        "year": year,
        "source": "manual_input",
        "note": "For accurate data, use VIN decoding"
    }

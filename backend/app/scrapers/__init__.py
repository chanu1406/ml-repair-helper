"""Web scrapers for vehicle listings"""

from backend.app.scrapers.base import BaseScraper
from backend.app.scrapers.cars_com import CarsComScraper
from backend.app.scrapers.autotrader import AutotraderScraper
from backend.app.scrapers.cargurus import CarGurusScraper

__all__ = [
    "BaseScraper",
    "CarsComScraper",
    "AutotraderScraper",
    "CarGurusScraper"
]

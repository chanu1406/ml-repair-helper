"""
SQLAlchemy models for vehicle data storage
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class VehicleSpecification(Base):
    """
    Vehicle specifications from NHTSA VIN decoding
    One record per unique VIN
    """
    __tablename__ = "vehicle_specifications"

    vin = Column(String(17), primary_key=True, index=True)
    make = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    trim = Column(String(100))
    body_type = Column(String(50))
    vehicle_type = Column(String(50))
    manufacturer = Column(String(100))

    # Engine & Drivetrain
    engine_cylinders = Column(Integer)
    engine_displacement = Column(String(20))
    fuel_type = Column(String(50))
    transmission = Column(String(50))
    drive_type = Column(String(20))

    # Additional specs
    doors = Column(Integer)
    plant_city = Column(String(100))
    plant_country = Column(String(50))

    # Metadata
    source = Column(String(20), default="NHTSA")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Raw data from NHTSA (JSON)
    raw_data = Column(JSON)

    # Relationships
    listings = relationship("VehicleListing", back_populates="specification")
    valuations = relationship("VehicleValuation", back_populates="specification")

    def __repr__(self):
        return f"<VehicleSpec(vin={self.vin}, {self.year} {self.make} {self.model})>"


class VehicleListing(Base):
    """
    Individual vehicle listings scraped from various sources
    Multiple listings per VIN (different prices, locations, conditions)
    """
    __tablename__ = "vehicle_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), ForeignKey("vehicle_specifications.vin"), index=True)

    # Pricing
    price = Column(Float, nullable=False)
    original_price = Column(Float)  # If discounted

    # Vehicle condition
    mileage = Column(Integer)
    condition = Column(String(20))  # new, used, certified

    # Location
    city = Column(String(100))
    state = Column(String(2), index=True)
    zip_code = Column(String(10))
    latitude = Column(Float)
    longitude = Column(Float)

    # Listing metadata
    source = Column(String(50), nullable=False, index=True)  # cars.com, autotrader, etc.
    listing_url = Column(Text)
    listing_id = Column(String(100))  # External ID from source site
    listing_date = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Additional fields
    dealer_name = Column(String(200))
    days_on_market = Column(Integer)
    features = Column(JSON)  # Additional features as JSON

    # Relationships
    specification = relationship("VehicleSpecification", back_populates="listings")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_make_model_year', 'vin', 'price'),
        Index('idx_location', 'state', 'city'),
        Index('idx_source_date', 'source', 'scraped_at'),
    )

    def __repr__(self):
        return f"<Listing(id={self.id}, vin={self.vin}, price=${self.price:,.0f}, source={self.source})>"


class VehicleValuation(Base):
    """
    Aggregated vehicle valuations calculated from market data
    One record per VIN (or make/model/year combination)
    Updated periodically based on latest listings
    """
    __tablename__ = "vehicle_valuations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(17), ForeignKey("vehicle_specifications.vin"), index=True, unique=True)

    # Valuation metrics
    retail_value = Column(Float)  # Average dealer price
    private_party_value = Column(Float)  # Average private seller price
    trade_in_value = Column(Float)  # Lower bound

    # Statistical data
    avg_price = Column(Float, nullable=False)
    median_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    std_dev = Column(Float)

    # Sample metadata
    sample_size = Column(Integer, default=0)  # Number of listings used
    avg_mileage = Column(Integer)
    mileage_range_min = Column(Integer)
    mileage_range_max = Column(Integer)

    # Geographic data
    regional_data = Column(JSON)  # Price variations by state/region

    # Temporal data
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    data_freshness_days = Column(Integer)  # Age of oldest listing used

    # Confidence
    confidence_score = Column(Float)  # 0-1 score based on sample size and variance

    # Relationships
    specification = relationship("VehicleSpecification", back_populates="valuations")

    def __repr__(self):
        return f"<Valuation(vin={self.vin}, avg_price=${self.avg_price:,.0f}, n={self.sample_size})>"


class ScraperLog(Base):
    """
    Log of scraping jobs for monitoring and debugging
    """
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20))  # running, completed, failed

    # Statistics
    listings_found = Column(Integer, default=0)
    listings_saved = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Details
    error_message = Column(Text)
    config = Column(JSON)  # Scraper configuration used

    def __repr__(self):
        return f"<ScraperLog(id={self.id}, source={self.source}, status={self.status})>"

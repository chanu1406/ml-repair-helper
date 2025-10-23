# Vehicle Valuation System - Documentation

## Overview

This system replaces hardcoded vehicle valuations with **real-time market data** from web scraping and official NHTSA vehicle specifications. It provides accurate, data-driven vehicle valuations for insurance claim cost predictions.

## Architecture

```
┌─────────────────┐
│  User Request   │
│  (with VIN)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         NHTSA API Service               │
│  - Decode VIN                           │
│  - Get vehicle specs (make/model/year)  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Valuation Service                  │
│  - Query market data from DB            │
│  - Calculate avg/median/retail prices   │
│  - Adjust for mileage & region          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Business Rules Engine              │
│  - Estimate repair costs                │
│  - Apply regional adjustments           │
│  - Return prediction + reasoning        │
└─────────────────────────────────────────┘
```

## Key Components

### 1. NHTSA API Service ([backend/app/nhtsa_service.py](backend/app/nhtsa_service.py))

**Purpose:** Decode VINs to get official vehicle specifications

**Features:**
- Free, official government API
- Returns make, model, year, trim, engine, body type, etc.
- Caching with `@lru_cache` for performance
- Error handling and validation

**Usage:**
```python
from backend.app.nhtsa_service import decode_vin

vehicle_data = decode_vin("4T1B11HK5KU211111")
# Returns: {make: "Toyota", model: "Camry", year: 2019, ...}
```

### 2. Database Models ([backend/app/database/models.py](backend/app/database/models.py))

**Tables:**

- **`vehicle_specifications`**: NHTSA-decoded vehicle specs (one per VIN)
- **`vehicle_listings`**: Scraped listings from Cars.com, Autotrader, etc.
- **`vehicle_valuations`**: Aggregated valuations calculated from listings
- **`scraper_logs`**: Scraping job history and statistics

**Key Relationships:**
```
VehicleSpecification (VIN)
    ├── VehicleListing (many listings per VIN)
    └── VehicleValuation (one valuation per VIN)
```

### 3. Web Scrapers ([backend/app/scrapers/](backend/app/scrapers/))

**Base Scraper** ([base.py](backend/app/scrapers/base.py)):
- Rate limiting (2 seconds between requests)
- Retry logic with exponential backoff
- Realistic browser headers
- Error handling and statistics

**Implemented Scrapers:**
- **Cars.com** ([cars_com.py](backend/app/scrapers/cars_com.py))
- **Autotrader** ([autotrader.py](backend/app/scrapers/autotrader.py))
- **CarGurus** ([cargurus.py](backend/app/scrapers/cargurus.py))

**Note:** These scrapers are **template implementations**. The actual HTML selectors need to be updated based on current website structures, as websites change frequently.

### 4. Data Processing Pipeline ([backend/app/pipeline/](backend/app/pipeline/))

**Data Processor** ([data_processor.py](backend/app/pipeline/data_processor.py)):
- Validates scraped listings
- Enriches data with NHTSA VIN decoding
- Saves to database
- Removes duplicates
- Cleans old listings

### 5. Valuation Service ([backend/app/valuation_service.py](backend/app/valuation_service.py))

**Smart Valuation Strategy:**

1. **Try VIN lookup** → Use exact market data for that VIN
2. **Try make/model/year lookup** → Use market data for similar vehicles
3. **Fallback to depreciation model** → Use hardcoded values from [enhanced_valuation.py](backend/app/enhanced_valuation.py)

**Adjustments:**
- Mileage adjustment (~$0.10 per mile difference from average)
- Regional price multipliers (CA: +25%, NY: +20%, MS: -15%, etc.)
- Sample size confidence scoring

**Returns:**
- Estimated value
- Retail value (top 1/3 of prices)
- Trade-in value (~75% of avg)
- Metadata (confidence, data source, sample size)

### 6. Updated Business Rules ([backend/app/business_rules.py](backend/app/business_rules.py))

**Changes:**
- Now accepts `vin` and `auto_mileage` fields
- Uses `get_vehicle_value()` instead of hardcoded `calculate_vehicle_value()`
- Falls back gracefully if no market data available

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python -c "from backend.app.database.session import init_db; init_db()"
```

Or the database will auto-initialize when you start the API server.

### 3. Test the System

```bash
python test_system.py
```

This tests:
- ✓ NHTSA API integration
- ✓ Database operations
- ✓ Valuation service
- ✓ Business rules integration

## Usage

### Run Web Scrapers

```bash
# Scrape Toyota Camry 2020 listings
python run_scraper.py --make Toyota --model Camry --year 2020 --max-results 50

# Scrape BMW 3 Series from specific sources
python run_scraper.py --make BMW --model "3 Series" --sources cars.com,autotrader

# Initialize DB first, then scrape
python run_scraper.py --make Honda --model Accord --init-db
```

**Options:**
- `--make`: Vehicle make (required)
- `--model`: Vehicle model (required)
- `--year`: Vehicle year (optional)
- `--max-results`: Max results per source (default: 100)
- `--sources`: Comma-separated sources (default: all)
- `--zip`: Search location ZIP (default: 10001)
- `--init-db`: Initialize database first

### API Endpoints

**Start API Server:**
```bash
cd backend
uvicorn app.main:app --reload
```

**New Endpoints:**

**1. Decode VIN**
```bash
GET /vehicle/decode/{vin}

Example:
curl http://localhost:8000/vehicle/decode/4T1B11HK5KU211111
```

**2. Get Vehicle Valuation**
```bash
GET /vehicle/value?vin=4T1B11HK5KU211111&mileage=50000&state=CA

# Or by make/model/year:
GET /vehicle/value?make=Toyota&model=Camry&year=2020&mileage=50000
```

**3. Predict with VIN**
```bash
POST /predict
{
  "features": {
    "vin": "4T1B11HK5KU211111",
    "auto_mileage": 50000,
    "incident_severity": "Major Damage",
    "collision_type": "Front Collision",
    "policy_state": "CA",
    "bodily_injuries": 1
  }
}
```

**Response includes:**
```json
{
  "predicted_cost": 18500,
  "estimated_vehicle_value": 24000,
  "confidence": "high",
  "reasoning": ["Major damage: 50% of vehicle value", ...],
  "valuation_details": {
    "data_source": "market_listings",
    "sample_size": 42,
    "confidence": "high"
  }
}
```

## Data Flow

### Initial Setup (Empty Database)

1. User provides VIN → NHTSA API decodes it
2. No market data available → Falls back to depreciation model
3. Returns estimate with `"data_source": "fallback_model"`

### After Scraping Data

1. Run scrapers for popular vehicles
2. Database fills with market listings
3. Valuation service uses **real prices** from scraped data
4. Returns estimate with `"data_source": "market_listings"`

### Continuous Improvement

1. Schedule daily/weekly scraper runs
2. Database stays fresh with current market prices
3. Valuations become more accurate over time
4. Old listings automatically cleaned up (90-day retention)

## Scraper Maintenance

### Important Notes

⚠️ **Web scrapers are fragile** - websites change their HTML structure frequently.

**When scrapers break:**

1. Inspect the target website's current HTML structure
2. Update CSS selectors in the respective scraper file
3. Test with small `--max-results` first
4. Consider using Selenium/Playwright for JavaScript-heavy sites

**Example inspection:**
```python
# In run_scraper.py or a test script:
from backend.app.scrapers import CarsComScraper

scraper = CarsComScraper()
url = "https://www.cars.com/shopping/results/?makes[]=toyota"
response = scraper._make_request(url)
soup = scraper._parse_html(response.text)

# Inspect the HTML to find correct selectors
print(soup.prettify())
```

### Ethical Scraping

- ✓ Respect `robots.txt`
- ✓ Use rate limiting (2+ seconds between requests)
- ✓ Use realistic User-Agent headers
- ✓ Don't overload servers
- ✓ Consider using official APIs when available

### Scraper Selectors to Update

Each scraper has placeholder selectors that need updating:

**Cars.com** ([cars_com.py](backend/app/scrapers/cars_com.py:96)):
```python
listing_elements = soup.find_all("div", class_="vehicle-card")  # Update this
```

**Autotrader** ([autotrader.py](backend/app/scrapers/autotrader.py:66)):
```python
listing_elements = soup.find_all("div", {"data-cmp": "inventoryListing"})  # Update this
```

**CarGurus** ([cargurus.py](backend/app/scrapers/cargurus.py:64)):
```python
listing_elements = soup.find_all("div", class_="listing-row")  # Update this
```

## Production Deployment

### Database Migration

For production, switch from SQLite to PostgreSQL:

1. Install PostgreSQL
2. Set environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost/vehicle_valuation"
```
3. Run migrations:
```bash
python -c "from backend.app.database.session import init_db; init_db()"
```

### Scheduled Scraping

Use Celery + Redis for background tasks:

1. Install Redis: `brew install redis` (Mac) or `sudo apt install redis` (Linux)
2. Configure Celery tasks in [backend/app/pipeline/scraper_tasks.py](backend/app/pipeline/scraper_tasks.py)
3. Run worker: `celery -A backend.app.pipeline.scraper_tasks worker --loglevel=info`
4. Schedule periodic tasks (daily scraping of popular models)

### Monitoring

Track:
- Scraper success rates ([scraper_logs](backend/app/database/models.py:256) table)
- Data freshness (valuation `last_updated` field)
- API response times
- Database size growth

## Advantages vs. Previous System

| Feature | Old System | New System |
|---------|-----------|------------|
| Data source | Hardcoded 2024 MSRP | Real market listings |
| Accuracy | Generic depreciation curves | Actual current prices |
| Coverage | 30 makes, generic values | Unlimited, real market data |
| VIN support | ❌ No | ✅ Yes (NHTSA API) |
| Regional pricing | Rough multipliers | Real location-based prices |
| Updates | Manual code changes | Automatic via scraping |
| Trim/options | ❌ Not considered | ✅ VIN includes trim |
| Confidence scoring | ❌ No | ✅ Based on sample size |

## Future Enhancements

1. **Add more scrapers**: Facebook Marketplace, Craigslist, TrueCar
2. **Scheduled jobs**: Automate daily scraping via Celery
3. **ML price prediction**: Train model on scraped data for even better estimates
4. **Price trend analysis**: Track how prices change over time
5. **VIN enrichment**: Automatically decode all VINs in historical claims dataset
6. **API rate limiting**: Add authentication and rate limits to API
7. **Caching layer**: Redis cache for frequently requested valuations

## Troubleshooting

### Import Errors

Make sure you're running from the project root:
```bash
cd /Users/chanuollala/Documents/ML/repair-helper-clean
python run_scraper.py ...
```

### Database Locked

If using SQLite and getting "database is locked":
- Close other connections
- Consider switching to PostgreSQL for concurrent access

### Scraper Returns Empty Results

- Website structure may have changed → Update selectors
- Rate limiting may be too aggressive → Check HTTP status codes
- Website may block scrapers → Try different User-Agent or use proxies

### NHTSA API Timeout

- NHTSA API is free but has rate limits
- Implement caching (already done with `@lru_cache`)
- Add retry logic for transient failures

## Files Created/Modified

### New Files
- `backend/app/nhtsa_service.py` - NHTSA VIN decoder
- `backend/app/valuation_service.py` - Market-based valuation
- `backend/app/database/` - Database models and session
- `backend/app/scrapers/` - Web scraping infrastructure
- `backend/app/pipeline/` - Data processing pipeline
- `run_scraper.py` - Scraper utility script
- `test_system.py` - System test suite
- `VEHICLE_VALUATION_README.md` - This file

### Modified Files
- `requirements.txt` - Added scraping and database dependencies
- `backend/app/business_rules.py` - Now uses valuation service
- `backend/app/schemas.py` - Added VIN and mileage fields
- `backend/app/main.py` - Added vehicle endpoints and DB initialization

### Unchanged (Fallback)
- `backend/app/enhanced_valuation.py` - Still used as fallback when no market data

## License & Legal

**Web Scraping:**
- Check each website's Terms of Service
- Respect robots.txt
- Use scraped data only for your insurance business purposes
- Do not redistribute scraped data

**NHTSA API:**
- Free, public government API
- No restrictions on use

---

**Questions or Issues?**

Check the code comments or run the test suite:
```bash
python test_system.py
```

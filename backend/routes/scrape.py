import logging
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Listing
from scrapers.base import SearchFilters
from scrapers.craigslist import CraigslistScraper
from scrapers.facebook import FacebookScraper
from services.geocoding import geocode_address, geocode_location, haversine_km, jitter_city_coords

logger = logging.getLogger(__name__)
router = APIRouter()

LISTING_TTL_HOURS = 24

_SCRAPERS = {
    "craigslist": CraigslistScraper,
    "facebook": FacebookScraper,
}


class ScrapeRequest(BaseModel):
    location: str
    radius_km: float = 5.0
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rooms: Optional[int] = None
    min_size_m2: Optional[float] = None
    max_size_m2: Optional[float] = None
    source: Literal["craigslist", "facebook"] = "craigslist"


@router.post("")
async def trigger_scrape(request: ScrapeRequest, db: Session = Depends(get_db)):
    center_lat, center_lng, city, country = geocode_location(request.location)
    if center_lat is None:
        raise HTTPException(status_code=422, detail=f"Could not geocode location: {request.location!r}")

    logger.info("Geocoded %r → %.4f, %.4f  city=%s", request.location, center_lat, center_lng, city)

    filters = SearchFilters(
        city=city,
        country=country,
        min_price=request.min_price,
        max_price=request.max_price,
        rooms=request.rooms,
        min_size_m2=request.min_size_m2,
        max_size_m2=request.max_size_m2,
    )

    scraper = _SCRAPERS[request.source]()

    try:
        raw_listings = await scraper.scrape(filters)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {exc}") from exc

    logger.info("Scraped %d raw listings for %s", len(raw_listings), city)

    saved = 0
    expires_at = datetime.utcnow() + timedelta(hours=LISTING_TTL_HOURS)

    for raw in raw_listings:
        if db.query(Listing).filter(Listing.external_id == raw.external_id).first():
            continue

        if raw.lat is not None and raw.lng is not None:
            # Precise coordinates from listing detail page — use directly
            lat, lng = raw.lat, raw.lng
        elif raw.address:
            lat, lng, is_precise = geocode_address(raw.address, city, country)
            # Area centroid (neighbourhood/suburb): jitter so markers don't stack
            if lat is not None and not is_precise:
                lat, lng = jitter_city_coords(lat, lng, raw.external_id)
        else:
            lat, lng = jitter_city_coords(center_lat, center_lng, raw.external_id)

        if lat is not None and lng is not None:
            distance_km = haversine_km(center_lat, center_lng, lat, lng)
            if distance_km > request.radius_km:
                logger.debug("Skipping listing %s outside radius (%.1f km)", raw.external_id, distance_km)
                continue

        db.add(
            Listing(
                source=raw.source,
                external_id=raw.external_id,
                title=raw.title,
                price=raw.price,
                currency=raw.currency,
                rooms=raw.rooms,
                size_m2=raw.size_m2,
                address=raw.address,
                city=city,
                country=country,
                lat=lat,
                lng=lng,
                url=raw.url,
                image_url=raw.image_url,
                scraped_at=datetime.utcnow(),
                expires_at=expires_at,
            )
        )
        saved += 1

    db.commit()
    logger.info("Saved %d new listings", saved)

    return {
        "scraped": len(raw_listings),
        "saved": saved,
        "city": city,
        "center_lat": center_lat,
        "center_lng": center_lng,
        "radius_km": request.radius_km,
    }

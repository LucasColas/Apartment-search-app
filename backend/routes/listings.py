from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models import Listing
from services.geocoding import haversine_km

router = APIRouter()


@router.get("")
def get_listings(
    center_lat: float = Query(...),
    center_lng: float = Query(...),
    radius_km: float = Query(default=5.0),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    rooms: Optional[int] = Query(default=None),
    min_size: Optional[float] = Query(default=None),
    max_size: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
):
    # Rough bounding box in SQL to reduce rows before exact distance check
    deg_margin = radius_km / 111.0
    q = db.query(Listing).filter(
        Listing.expires_at > datetime.utcnow(),
        Listing.lat.between(center_lat - deg_margin, center_lat + deg_margin),
        Listing.lng.between(center_lng - deg_margin * 2, center_lng + deg_margin * 2),
    )
    if min_price is not None:
        q = q.filter(or_(Listing.price >= min_price, Listing.price.is_(None)))
    if max_price is not None:
        q = q.filter(or_(Listing.price <= max_price, Listing.price.is_(None)))
    if rooms is not None:
        q = q.filter(or_(Listing.rooms == rooms, Listing.rooms.is_(None)))
    if min_size is not None:
        q = q.filter(or_(Listing.size_m2 >= min_size, Listing.size_m2.is_(None)))
    if max_size is not None:
        q = q.filter(or_(Listing.size_m2 <= max_size, Listing.size_m2.is_(None)))

    candidates = q.order_by(Listing.scraped_at.desc()).all()

    listings = [
        l for l in candidates
        if l.lat is not None and l.lng is not None
        and haversine_km(center_lat, center_lng, l.lat, l.lng) <= radius_km
    ]

    return {
        "listings": [_serialize(l) for l in listings],
        "total": len(listings),
    }


def _serialize(l: Listing) -> dict:
    return {
        "id": l.id,
        "source": l.source,
        "title": l.title,
        "price": l.price,
        "currency": l.currency,
        "rooms": l.rooms,
        "size_m2": l.size_m2,
        "address": l.address,
        "city": l.city,
        "country": l.country,
        "lat": l.lat,
        "lng": l.lng,
        "url": l.url,
        "image_url": l.image_url,
        "scraped_at": l.scraped_at.isoformat() if l.scraped_at else None,
    }

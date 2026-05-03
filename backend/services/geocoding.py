import hashlib
import math
import time
import logging
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

logger = logging.getLogger(__name__)

_geocoder = Nominatim(user_agent="apartment-search-app/1.0", timeout=10)
_last_call: float = 0.0


def _throttle() -> None:
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_call = time.time()


# Nominatim addresstype values that indicate a precise street/building-level result.
# Anything else (neighbourhood, suburb, city, …) is an area centroid.
_PRECISE_ADDRESS_TYPES = frozenset({"house", "building", "road", "residential", "street"})


def geocode_address(
    address: Optional[str], city: str, country: str
) -> tuple[Optional[float], Optional[float], bool]:
    """Return (lat, lng, is_precise).

    is_precise is True only when Nominatim resolved to a street or building,
    not to a neighbourhood/suburb/area centroid.
    """
    _throttle()
    query = f"{address}, {city}, {country}" if address else f"{city}, {country}"
    try:
        location = _geocoder.geocode(query)
        if location:
            address_type = location.raw.get("addresstype", "")
            is_precise = address_type in _PRECISE_ADDRESS_TYPES
            logger.debug(
                "Geocoded %r → %.4f, %.4f (addresstype=%s, precise=%s)",
                query, location.latitude, location.longitude, address_type, is_precise,
            )
            return location.latitude, location.longitude, is_precise
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.warning("Geocoding failed for '%s': %s", query, e)
    return None, None, False


def geocode_location(location: str) -> tuple[Optional[float], Optional[float], str, str]:
    """Geocode a free-form location string and extract city + country from the result."""
    _throttle()
    try:
        result = _geocoder.geocode(location, addressdetails=True)
        if result:
            addr = result.raw.get("address", {})
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("municipality")
                or addr.get("county")
                or location.split(",")[0].strip()
            )
            country = addr.get("country", "")
            return result.latitude, result.longitude, city, country
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.warning("Geocoding failed for '%s': %s", location, e)
    return None, None, "", ""


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the great-circle distance in kilometres between two points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


# ~1 km radius jitter so stacked city-center markers are distinguishable
_JITTER_DEGREES = 0.009


def jitter_city_coords(
    lat: float, lng: float, seed: str
) -> tuple[float, float]:
    """Apply deterministic sub-km jitter to city-center coordinates.

    Listings without a street address all get the same city lat/lng, which
    makes them overlap into a single dot. Using the listing's external_id as
    seed gives each one a stable, unique offset within ~1 km of the center.
    """
    digest = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    # Two independent offsets in [-1, 1] from the digest
    lat_off = ((digest & 0xFFFF) / 0xFFFF * 2 - 1) * _JITTER_DEGREES
    lng_off = (((digest >> 16) & 0xFFFF) / 0xFFFF * 2 - 1) * _JITTER_DEGREES
    return round(lat + lat_off, 6), round(lng + lng_off, 6)

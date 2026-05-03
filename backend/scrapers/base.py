from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchFilters:
    city: str
    country: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rooms: Optional[int] = None
    min_size_m2: Optional[float] = None
    max_size_m2: Optional[float] = None


@dataclass
class RawListing:
    external_id: str
    source: str
    url: str
    title: str = ""
    price: Optional[float] = None
    currency: str = "USD"
    rooms: Optional[int] = None
    size_m2: Optional[float] = None
    address: Optional[str] = None
    image_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, filters: SearchFilters) -> list[RawListing]:
        """Scrape listings matching the given filters."""

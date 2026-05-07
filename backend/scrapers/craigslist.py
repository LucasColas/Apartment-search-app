import asyncio
import hashlib
import json as json_lib
import logging
import random
import re
import unicodedata
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, RawListing, SearchFilters

logger = logging.getLogger(__name__)

SQM_TO_SQFT = 10.764

CITY_SUBDOMAINS: dict[str, str] = {
    # North America
    "new york": "newyork",
    "los angeles": "losangeles",
    "chicago": "chicago",
    "houston": "houston",
    "phoenix": "phoenix",
    "philadelphia": "philadelphia",
    "san antonio": "sanantonio",
    "san diego": "sandiego",
    "dallas": "dallas",
    "san francisco": "sfbay",
    "san jose": "sfbay",
    "seattle": "seattle",
    "denver": "denver",
    "boston": "boston",
    "miami": "miami",
    "atlanta": "atlanta",
    "minneapolis": "minneapolis",
    "portland": "portland",
    "las vegas": "lasvegas",
    "toronto": "toronto",
    "montreal": "montreal",
    "vancouver": "vancouver",
    "calgary": "calgary",
    "ottawa": "ottawa",
    # Europe
    "london": "london",
    "paris": "paris",
    "berlin": "berlin",
    "amsterdam": "amsterdam",
    "brussels": "brussels",
    "vienna": "vienna",
    "zurich": "zurich",
    "rome": "rome",
    "madrid": "madrid",
    "barcelona": "barcelona",
}

# Each profile contains the headers that are specific to a given browser.
# Sec-Ch-Ua and Sec-Ch-Ua-Platform are only sent by Chromium-based browsers.
_BROWSER_PROFILES: list[dict[str, str]] = [
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Sec-Ch-Ua": '"Chromium";v="123", "Google Chrome";v="123", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Sec-Ch-Ua": '"Chromium";v="122", "Google Chrome";v="122", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0"
        ),
    },
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.4 Safari/605.1.15"
        ),
    },
]

# Headers every browser sends on a normal page navigation.
_COMMON_HEADERS: dict[str, str] = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def _make_headers(referer: Optional[str] = None) -> dict[str, str]:
    """Return a randomised but internally consistent set of browser headers."""
    headers = {**_COMMON_HEADERS, **random.choice(_BROWSER_PROFILES)}
    # Sec-Fetch-Site reflects how the user arrived at the page.
    headers["Sec-Fetch-Site"] = "same-origin" if referer else "none"
    if referer:
        headers["Referer"] = referer
    return headers


_DETAIL_DELAY_RANGE = (0.5, 1.5)
_RATE_LIMIT_BACKOFF = 30.0

# Craigslist post IDs are always 10 digits
_LISTING_ID_RE = re.compile(r"/(\d{10})(?:\.html)?(?:[?#]|$)")

# Price: currency symbol + number with optional space/comma thousands separator
# e.g. "$1 075", "$1,500", "€800"
_PRICE_RE = re.compile(r"([$£€])\s*(\d{1,3}(?:[,\s]\d{3})*|\d+)")

# Bedrooms: digit + keyword ("2br", "2 bed", "2 bedrooms", "2 chambres")
_BEDROOM_RE = re.compile(r"(\d+)\s*(?:br\b|bed(?:room)?s?\b|chambre?s?\b)", re.IGNORECASE)

# Bedrooms: English word ("one-bedroom", "two bedroom")
_WORD_BEDROOM_RE = re.compile(
    r"\b(one|two|three|four|five|six)\s*[-\s]?bedroom", re.IGNORECASE
)
_WORD_TO_INT: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6
}

# Quebec "X 1/2" pieces notation: 3½=1br, 4½=2br; also handles "3.5" decimal form
_PIECES_RE = re.compile(r"(\d+)(?:\.5\b|\s*(?:½|1/2)\b)")

# Square footage
_SQFT_RE = re.compile(r"([\d,]+)\s*(?:ft[²2]?|sqft|sq\.?\s*ft)\b", re.IGNORECASE)

class CraigslistScraper(BaseScraper):
    _SEARCH_URL = "https://{subdomain}.craigslist.org/search/apa"

    @staticmethod
    def _normalize(city: str) -> str:
        """Strip accents and lowercase so 'Montréal' matches 'montreal'."""
        nfkd = unicodedata.normalize("NFKD", city)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    def _subdomain(self, city: str) -> str:
        normalized = self._normalize(city)
        return CITY_SUBDOMAINS.get(normalized, normalized.replace(" ", ""))

    def _build_url(self, subdomain: str, filters: SearchFilters) -> str:
        params: dict[str, int] = {}
        if filters.min_price is not None:
            params["min_price"] = int(filters.min_price)
        if filters.max_price is not None:
            params["max_price"] = int(filters.max_price)
        if filters.rooms is not None:
            params["min_bedrooms"] = filters.rooms
            params["max_bedrooms"] = filters.rooms
        if filters.min_size_m2 is not None:
            params["minSqft"] = int(filters.min_size_m2 * SQM_TO_SQFT)
        if filters.max_size_m2 is not None:
            params["maxSqft"] = int(filters.max_size_m2 * SQM_TO_SQFT)

        base = self._SEARCH_URL.format(subdomain=subdomain)
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base}?{qs}" if qs else base

    async def scrape(self, filters: SearchFilters) -> list[RawListing]:
        subdomain = self._subdomain(filters.city)
        url = self._build_url(subdomain, filters)
        logger.info("Craigslist scrape -> %s", url)

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers=_make_headers())
            response.raise_for_status()
            logger.info("Craigslist response: %d bytes", len(response.text))

            listings = self._parse(response.text, subdomain)
            logger.info("Craigslist: fetching detail pages for %d listings", len(listings))

            semaphore = asyncio.Semaphore(5)
            details = await asyncio.gather(
                *[self._fetch_detail(l.url, client, semaphore, referer=url) for l in listings]
            )

        for listing, detail in zip(listings, details):
            if detail.get("lat") is not None:
                listing.lat = detail["lat"]
                listing.lng = detail["lng"]
            if detail.get("address"):
                listing.address = detail["address"]
            if detail.get("rooms") is not None:
                listing.rooms = detail["rooms"]

        return listings

    async def _fetch_detail(
        self,
        url: str,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        referer: str,
    ) -> dict:
        """Fetch a listing page and extract ld+json structured data (coords, address, bedrooms)."""
        async with semaphore:
            await asyncio.sleep(random.uniform(*_DETAIL_DELAY_RANGE))
            try:
                resp = await client.get(url, timeout=15, headers=_make_headers(referer))
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", _RATE_LIMIT_BACKOFF))
                    logger.warning(
                        "Rate limited on %s; backing off %.0fs", url[:70], retry_after
                    )
                    await asyncio.sleep(retry_after)
                    resp = await client.get(url, timeout=15, headers=_make_headers(referer))
                if resp.status_code != 200:
                    logger.debug("Non-200 status %d for %s", resp.status_code, url[:70])
                    return {}
                soup = BeautifulSoup(resp.text, "lxml")
                script = soup.find("script", {"id": "ld_posting_data"})
                if not script:
                    return {}
                raw = script.get_text(strip=True)
                if not raw:
                    return {}
                data = json_lib.loads(raw)

                result: dict = {}
                if "latitude" in data and "longitude" in data:
                    result["lat"] = float(data["latitude"])
                    result["lng"] = float(data["longitude"])
                if "numberOfBedrooms" in data:
                    try:
                        result["rooms"] = int(data["numberOfBedrooms"])
                    except (ValueError, TypeError):
                        pass
                addr = data.get("address", {})
                street = addr.get("streetAddress", "").strip()
                locality = addr.get("addressLocality", "").strip()
                postal = addr.get("postalCode", "").strip()
                if street:
                    result["address"] = ", ".join(filter(None, [street, locality, postal]))

                logger.info(
                    "  detail lat=%.4f lng=%.4f address=%r rooms=%s | %s",
                    result.get("lat", 0), result.get("lng", 0),
                    result.get("address"), result.get("rooms"), url[:70],
                )
                return result
            except Exception as exc:
                logger.debug("Detail fetch failed for %s: %s", url, exc)
                return {}

    # ── HTML parsing ──────────────────────────────────────────────────────────

    def _parse(self, html: str, subdomain: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")

        # Try newest layout first, then legacy selectors
        items = (
            soup.select("li.cl-static-search-result")
            or soup.select("li.cl-search-result")
            or soup.select("li.result-row")
        )
        if items:
            logger.info("Craigslist: %d structured items", len(items))
            results = [r for item in items if (r := self._parse_item(item, subdomain))]
            if results:
                return results

        logger.info("Craigslist: structured selectors empty, falling back to URL pattern")
        return self._parse_by_url_pattern(soup, subdomain)

    def _parse_item(self, item, subdomain: str) -> Optional[RawListing]:
        link = item.find("a")
        if not link:
            return None

        href = link.get("href", "")
        url = f"https://{subdomain}.craigslist.org{href}" if href.startswith("/") else href
        m = _LISTING_ID_RE.search(url)
        external_id = m.group(1) if m else hashlib.md5(url.encode()).hexdigest()[:12]

        # Title: li 'title' attr is clean (no price/location appended)
        title = item.get("title") or ""
        if not title:
            title_el = link.select_one("div.title")
            title = title_el.get_text(strip=True) if title_el else ""

        # Price from dedicated element
        price_el = link.select_one("div.price")
        price_text = price_el.get_text(" ", strip=True) if price_el else ""
        price, currency = self._extract_price(price_text)

        # Location label from dedicated element — used as address for geocoding
        location_el = link.select_one("div.location")
        address = location_el.get_text(strip=True) if location_el else None
        address = address or None

        rooms = self._extract_rooms(title)
        size_m2 = self._extract_size_m2(title)

        image_el = item.select_one("img")
        image_url = image_el.get("src") if image_el else None

        logger.info(
            "  [%s] title=%r | address=%r | price=%s %s | rooms=%s | size_m2=%s",
            external_id, title, address, price, currency, rooms, size_m2,
        )

        return RawListing(
            external_id=external_id,
            source="craigslist",
            url=url,
            title=title,
            price=price,
            currency=currency,
            rooms=rooms,
            size_m2=size_m2,
            address=address,
            image_url=image_url,
        )

    def _parse_by_url_pattern(self, soup, subdomain: str) -> list[RawListing]:
        """Fallback for unknown HTML layouts: find anchors whose href contains a 10-digit ID."""
        seen: set[str] = set()
        results: list[RawListing] = []

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            m = _LISTING_ID_RE.search(href)
            if not m:
                continue
            external_id = m.group(1)
            if external_id in seen:
                continue
            seen.add(external_id)

            url = (
                f"https://{subdomain}.craigslist.org{href}"
                if href.startswith("/")
                else href
            )

            # Extract location from div.location if present inside the anchor
            location_el = anchor.select_one("div.location")
            address = location_el.get_text(strip=True) if location_el else None
            address = address or None

            full_text = anchor.get_text(" ", strip=True)
            title = self._extract_title(full_text)
            price, currency = self._extract_price(full_text)
            rooms = self._extract_rooms(full_text)
            size_m2 = self._extract_size_m2(full_text)

            results.append(
                RawListing(
                    external_id=external_id,
                    source="craigslist",
                    url=url,
                    title=title,
                    price=price,
                    currency=currency,
                    rooms=rooms,
                    size_m2=size_m2,
                    address=address,
                )
            )

        logger.info("Craigslist URL-pattern fallback: %d listings", len(results))
        return results

    # ── Field extractors ──────────────────────────────────────────────────────

    def _extract_price(self, text: str) -> tuple[Optional[float], str]:
        m = _PRICE_RE.search(text)
        if not m:
            return None, "USD"
        price = float(re.sub(r"[,\s]", "", m.group(2)))
        currency = {"£": "GBP", "€": "EUR"}.get(m.group(1), "USD")
        return price, currency

    def _extract_title(self, text: str) -> str:
        """Everything before the first price symbol is the listing title."""
        m = _PRICE_RE.search(text)
        title = text[: m.start()].strip() if m else text[:80].strip()
        return title or text[:80]

    def _extract_rooms(self, text: str) -> Optional[int]:
        m = _BEDROOM_RE.search(text)
        if m:
            return int(m.group(1))
        m = _WORD_BEDROOM_RE.search(text)
        if m:
            return _WORD_TO_INT[m.group(1).lower()]
        # Quebec "X 1/2" / "X.5" pieces: 3½=1br, 4½=2br, 5½=3br
        m = _PIECES_RE.search(text)
        if m:
            pieces = int(m.group(1))
            return max(0, pieces - 2)
        return None

    def _extract_size_m2(self, text: str) -> Optional[float]:
        m = _SQFT_RE.search(text)
        if not m:
            return None
        return round(float(m.group(1).replace(",", "")) / SQM_TO_SQFT, 1)

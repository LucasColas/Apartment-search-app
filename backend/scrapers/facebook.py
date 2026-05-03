import asyncio
import re
import time
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup

from .base import BaseScraper, RawListing, SearchFilters

# Persistent browser profile so Facebook session survives between runs.
# Run once with headless=False to log in — session is reused automatically after that.
BROWSER_PROFILE_DIR = Path(__file__).parent.parent.parent / ".browser_profile"


class FacebookScraper(BaseScraper):
    _BASE_URL = "https://www.facebook.com/marketplace/{city}/propertyrentals"

    def _build_url(self, filters: SearchFilters) -> str:
        city_slug = filters.city.lower().replace(" ", "-")
        params: list[str] = []
        if filters.min_price is not None:
            params.append(f"minPrice={int(filters.min_price)}")
        if filters.max_price is not None:
            params.append(f"maxPrice={int(filters.max_price)}")
        if filters.rooms is not None:
            params.append(f"minBedrooms={filters.rooms}")
        base = self._BASE_URL.format(city=city_slug)
        return f"{base}?{'&'.join(params)}" if params else base

    async def scrape(self, filters: SearchFilters) -> list[RawListing]:
        # Playwright's async API requires subprocess creation, which fails on Windows
        # under uvicorn's SelectorEventLoop even with ProactorEventLoopPolicy patches
        # (uvicorn reload workers create their own loop before any policy takes effect).
        # Solution: use the sync API in a thread — no asyncio involvement at all.
        return await asyncio.to_thread(self._scrape_sync, filters)

    def _scrape_sync(self, filters: SearchFilters) -> list[RawListing]:
        from playwright.sync_api import sync_playwright  # lazy to avoid import-time side effects

        BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        url = self._build_url(filters)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(BROWSER_PROFILE_DIR),
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else context.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            time.sleep(3)

            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

            content = page.content()
            context.close()

        return self._parse(content)

    def _parse(self, html: str) -> list[RawListing]:
        soup = BeautifulSoup(html, "lxml")
        items = soup.select("a[href*='/marketplace/item/']")
        seen: set[str] = set()
        results: list[RawListing] = []
        for item in items:
            listing = self._parse_item(item)
            if listing and listing.external_id not in seen:
                seen.add(listing.external_id)
                results.append(listing)
        return results

    def _parse_item(self, anchor) -> Optional[RawListing]:
        href = anchor.get("href", "")
        match = re.search(r"/marketplace/item/(\d+)", href)
        if not match:
            return None
        external_id = match.group(1)
        url = f"https://www.facebook.com{href}" if href.startswith("/") else href

        texts = [s.strip() for s in anchor.stripped_strings if s.strip()]
        title = texts[0] if texts else "Facebook Listing"

        price = None
        currency = "USD"
        for text in texts:
            m = re.search(r"([£€$]?)\s*([\d,]+)", text)
            if m and int(m.group(2).replace(",", "")) > 50:
                price = float(m.group(2).replace(",", ""))
                currency = {"£": "GBP", "€": "EUR"}.get(m.group(1), "USD")
                break

        image = anchor.select_one("img")
        image_url = image.get("src") if image else None

        return RawListing(
            external_id=external_id,
            source="facebook",
            url=url,
            title=title,
            price=price,
            currency=currency,
            image_url=image_url,
        )

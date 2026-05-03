"""Run this to diagnose the scraper without starting the full server.
Usage: python backend/debug_scraper.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import httpx
from bs4 import BeautifulSoup

from scrapers.craigslist import CraigslistScraper
from scrapers.base import SearchFilters
from services.geocoding import geocode_address
from database import SessionLocal, engine
from models import Base, Listing

Base.metadata.create_all(bind=engine)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


async def check_raw_html():
    """Fetch the Craigslist page and print raw item text so we can see what the parser receives."""
    print("=== Raw Craigslist HTML (first 5 items) ===")
    url = "https://montreal.craigslist.org/search/apa?min_price=500&max_price=2000"
    print(f"Fetching: {url}\n")
    async with httpx.AsyncClient(headers=_HEADERS, timeout=30, follow_redirects=True) as client:
        resp = await client.get(url)
    print(f"Status: {resp.status_code}  ({len(resp.text)} bytes)\n")

    soup = BeautifulSoup(resp.text, "lxml")
    items = soup.select("li.cl-search-result") or soup.select("li.result-row")
    print(f"Items found with structured selector: {len(items)}\n")

    for i, item in enumerate(items[:5]):
        print(f"--- item {i} ---")
        print(f"  raw text : {item.get_text(' ', strip=True)[:200]}")
        print(f"  inner HTML snippet:\n{item.prettify()[:600]}\n")


async def check_scraper():
    print("\n=== Parsed listings (first 10) ===")
    scraper = CraigslistScraper()
    filters = SearchFilters(city="Montreal", country="Canada", min_price=500, max_price=2000)
    url = scraper._build_url(scraper._subdomain("Montreal"), filters)
    print(f"URL: {url}\n")

    try:
        results = await scraper.scrape(filters)
        print(f"Total parsed: {len(results)}\n")
        for r in results[:10]:
            print(
                f"  title   : {r.title[:70]}\n"
                f"  address : {r.address}\n"
                f"  price   : {r.price} {r.currency}\n"
                f"  rooms   : {r.rooms}  size_m2={r.size_m2}\n"
                f"  url     : {r.url[:80]}\n"
            )
    except Exception as e:
        print(f"ERROR: {e}")


def check_db():
    print("\n=== DB contents ===")
    db = SessionLocal()
    total = db.query(Listing).count()
    print(f"Total listings in DB: {total}")
    for l in db.query(Listing).limit(5).all():
        print(f"  [{l.source}] {l.city} | price={l.price} | lat={l.lat} | lng={l.lng} | address={l.address}")
    db.close()


def check_geocoding():
    print("\n=== Testing geocoding ===")
    lat, lng, precise = geocode_address("Plateau-Mont-Royal", "Montreal", "Canada")
    print(f"Plateau-Mont-Royal → lat={lat}, lng={lng}, precise={precise}")
    lat, lng, precise = geocode_address("5870 Avenue Mcshane", "Montreal", "Canada")
    print(f"5870 Avenue Mcshane → lat={lat}, lng={lng}, precise={precise}")


async def main():
    await check_raw_html()
    await check_scraper()
    check_db()
    check_geocoding()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

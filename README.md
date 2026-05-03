# Apartment Search App

A web app that scrapes apartment listings from Craigslist and Facebook Marketplace, geocodes addresses, and visualises results on an interactive map with price/size/room filters.

**Stack:** FastAPI + SQLite (backend) · React + Vite + Leaflet (frontend)

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| [uv](https://github.com/astral-sh/uv) | latest |
| Node.js | 18+ |
| npm | 9+ |

---

## Installation

### Backend

```bash
# Create and activate the virtual environment
uv venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS / Linux

# Install Python dependencies
uv pip install -r requirements.txt

# Install Playwright browsers (required for Facebook scraper)
playwright install chromium
```

### Frontend

```bash
cd frontend
npm install
```

---

## Running

Open two terminals from the project root.

**Terminal 1 — backend** (runs on `http://localhost:8000`):

```bash
.venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS / Linux

cd backend
python run.py
```

**Terminal 2 — frontend** (runs on `http://localhost:5173`):

```bash
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser.

---

## Database

SQLite is used and created automatically on first run at `backend/apartments.db`. No migration step is needed.

Listings expire after **24 hours** and are filtered out automatically.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/listings` | Search listings with filters |
| `POST` | `/scrape` | Trigger a scrape for a location |

### `GET /listings` query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `center_lat` | float | Latitude of search centre |
| `center_lng` | float | Longitude of search centre |
| `radius_km` | float | Search radius in kilometres |
| `min_price` | int | Minimum monthly rent |
| `max_price` | int | Maximum monthly rent |
| `rooms` | int | Number of rooms |
| `min_size` | float | Minimum size in m² |
| `max_size` | float | Maximum size in m² |

### `POST /scrape` request body

```json
{
  "location": "Montreal, Canada",
  "radius_km": 5.0,
  "min_price": 500,
  "max_price": 5000,
  "rooms": 2,
  "min_size_m2": 30,
  "max_size_m2": 100,
  "source": "craigslist"
}
```

`source` is either `"craigslist"` or `"facebook"`.

---

## Scrapers

### Craigslist
Uses `httpx` + `BeautifulSoup`. Works out of the box with no extra setup.

### Facebook Marketplace
Uses Playwright with a persistent browser profile stored in `.browser_profile/`. The first run will open a browser window — log in to Facebook manually, then close it. Subsequent runs reuse the saved session.

---

## Geocoding

Addresses are resolved via [Nominatim](https://nominatim.org/) (OpenStreetMap). The service enforces a **1 request/second** rate limit, so large scrapes may take time to geocode.

---

## Diagnostics

```bash
cd backend
python debug_scraper.py
```

Runs end-to-end checks on the scraper, database contents, and geocoding service.

---

## Project Structure

```
├── backend/
│   ├── run.py              # Uvicorn entry point
│   ├── main.py             # FastAPI app + CORS
│   ├── database.py         # SQLAlchemy engine & session
│   ├── models.py           # Listing ORM model
│   ├── routes/
│   │   ├── listings.py     # GET /listings
│   │   └── scrape.py       # POST /scrape
│   ├── scrapers/
│   │   ├── base.py         # BaseScraper interface
│   │   ├── craigslist.py
│   │   └── facebook.py
│   └── services/
│       └── geocoding.py    # Nominatim with rate limiting
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── MapView.jsx
│   │   │   ├── SearchPanel.jsx
│   │   │   ├── ListingsList.jsx
│   │   │   └── ListingCard.jsx
│   │   └── hooks/
│   │       ├── useListings.js
│   │       └── useLocationSearch.js
│   └── vite.config.js      # Proxies /api → localhost:8000
├── requirements.txt
└── README.md
```

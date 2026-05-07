import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

from database import Base, engine
from routes import listings, scrape

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Apartment Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router, prefix="/listings", tags=["listings"])
app.include_router(scrape.router, prefix="/scrape", tags=["scrape"])


@app.get("/health")
def health():
    return {"status": "ok"}

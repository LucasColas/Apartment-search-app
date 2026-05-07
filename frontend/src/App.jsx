import { useState } from "react";
import SearchPanel from "./components/SearchPanel";
import MapView from "./components/MapView";
import ListingsList from "./components/ListingsList";
import { useListings } from "./hooks/useListings";

export default function App() {
  const { listings, loading, error, scrapeResult, searchCenter, searchRadius, scrapeAndFetch } = useListings();
  const [highlightedId, setHighlightedId] = useState(null);
  const [selectedCenter, setSelectedCenter] = useState(null);

  const handleSearch = async (filters) => {
    setSelectedCenter(null);
    await scrapeAndFetch(filters);
  };

  const handleSelect = (listing) => {
    setHighlightedId(listing.id);
    if (listing.lat && listing.lng) setSelectedCenter([listing.lat, listing.lng]);
  };

  const firstGeo = listings.find((l) => l.lat && l.lng);
  const derivedCenter =
    selectedCenter ?? searchCenter ?? (firstGeo ? [firstGeo.lat, firstGeo.lng] : null);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50">
      <aside className="w-80 flex-shrink-0 flex flex-col border-r border-slate-200 bg-white">
        <SearchPanel onSearch={handleSearch} loading={loading} />

        {error && (
          <div className="mx-4 mb-2 p-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs">
            {error}
          </div>
        )}

        {scrapeResult && !loading && (
          <div className="mx-4 mb-2 p-2 rounded-lg bg-green-50 border border-green-200 text-green-700 text-xs">
            Scraped {scrapeResult.scraped} — saved {scrapeResult.saved} new listings
          </div>
        )}

        <div className="flex-1 overflow-y-auto border-t border-slate-100">
          <ListingsList
            listings={listings}
            highlightedId={highlightedId}
            onSelect={handleSelect}
          />
        </div>
      </aside>

      <main className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/60 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-slate-600">Scraping listings…</p>
            </div>
          </div>
        )}
        <MapView
          listings={listings}
          center={derivedCenter}
          radiusKm={selectedCenter ? null : searchRadius}
          highlightedId={highlightedId}
          onMarkerClick={handleSelect}
        />
      </main>
    </div>
  );
}

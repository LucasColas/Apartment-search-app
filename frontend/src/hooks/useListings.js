import { useState } from "react";
import axios from "axios";

export function useListings() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scrapeResult, setScrapeResult] = useState(null);
  const [searchCenter, setSearchCenter] = useState(null);
  const [searchRadius, setSearchRadius] = useState(null);

  const scrapeAndFetch = async (filters) => {
    setLoading(true);
    setError(null);
    setScrapeResult(null);

    try {
      const { data: scrapeData } = await axios.post("/api/scrape", filters);
      console.log("[scrape]", scrapeData);
      setScrapeResult(scrapeData);

      const center = [scrapeData.center_lat, scrapeData.center_lng];
      setSearchCenter(center);
      setSearchRadius(scrapeData.radius_km);

      const params = Object.fromEntries(
        Object.entries({
          center_lat: scrapeData.center_lat,
          center_lng: scrapeData.center_lng,
          radius_km: scrapeData.radius_km,
          min_price: filters.min_price,
          max_price: filters.max_price,
          rooms: filters.rooms,
          min_size: filters.min_size_m2,
          max_size: filters.max_size_m2,
        }).filter(([, v]) => v != null && v !== "")
      );

      const { data } = await axios.get("/api/listings", { params });
      console.log("[listings]", data);
      setListings(data.listings ?? []);
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  return { listings, loading, error, scrapeResult, searchCenter, searchRadius, scrapeAndFetch };
}

import { useState, useRef } from "react";
import { useLocationSearch } from "../hooks/useLocationSearch";

const SOURCES = [
  { value: "craigslist", label: "Craigslist" },
  { value: "facebook", label: "Facebook Marketplace" },
];

const ROOM_OPTIONS = [1, 2, 3, 4];

export default function SearchPanel({ onSearch, loading }) {
  const [form, setForm] = useState({
    location: "",
    radius_km: 5,
    min_price: "",
    max_price: "",
    rooms: "",
    min_size_m2: "",
    max_size_m2: "",
    source: "craigslist",
  });

  const [query, setQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef(null);
  const { suggestions, loading: suggestionsLoading } = useLocationSearch(query);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleLocationInput = (e) => {
    const val = e.target.value;
    setForm((f) => ({ ...f, location: val }));
    setQuery(val);
    setShowSuggestions(true);
  };

  const handleSuggestionSelect = (suggestion) => {
    setForm((f) => ({ ...f, location: suggestion.display_name }));
    setQuery("");
    setShowSuggestions(false);
    inputRef.current?.blur();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowSuggestions(false);
    const payload = {
      location: form.location,
      radius_km: Number(form.radius_km),
      source: form.source,
      min_price: form.min_price !== "" ? Number(form.min_price) : null,
      max_price: form.max_price !== "" ? Number(form.max_price) : null,
      rooms: form.rooms !== "" ? Number(form.rooms) : null,
      min_size_m2: form.min_size_m2 !== "" ? Number(form.min_size_m2) : null,
      max_size_m2: form.max_size_m2 !== "" ? Number(form.max_size_m2) : null,
    };
    onSearch(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-4 h-full overflow-y-auto">
      <h1 className="text-xl font-bold text-slate-800">Apartment Search</h1>

      {/* Location autocomplete */}
      <fieldset className="flex flex-col gap-1 relative">
        <label className="label">Location *</label>
        <input
          ref={inputRef}
          className="input"
          placeholder="e.g. Montmartre, Paris or 5th Ave, New York"
          value={form.location}
          onChange={handleLocationInput}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          required
          autoComplete="off"
        />
        {showSuggestions && (suggestions.length > 0 || suggestionsLoading) && (
          <ul className="absolute top-full left-0 right-0 z-50 bg-white border border-slate-200 rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto">
            {suggestionsLoading && (
              <li className="px-3 py-2 text-xs text-slate-400">Searching…</li>
            )}
            {suggestions.map((s) => (
              <li
                key={s.place_id}
                onMouseDown={() => handleSuggestionSelect(s)}
                className="px-3 py-2 text-sm text-slate-700 hover:bg-blue-50 cursor-pointer border-b border-slate-100 last:border-0"
              >
                {s.display_name}
              </li>
            ))}
          </ul>
        )}
      </fieldset>

      {/* Radius slider */}
      <fieldset className="flex flex-col gap-1">
        <label className="label">
          Radius: <span className="font-semibold text-blue-600">{form.radius_km} km</span>
        </label>
        <input
          type="range"
          min={1}
          max={20}
          step={1}
          value={form.radius_km}
          onChange={set("radius_km")}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-slate-400">
          <span>1 km</span>
          <span>20 km</span>
        </div>
      </fieldset>

      {/* Price */}
      <fieldset className="flex flex-col gap-1">
        <label className="label">Budget ($/€/£ / month)</label>
        <div className="flex gap-2">
          <input className="input" placeholder="Min" type="number" value={form.min_price} onChange={set("min_price")} />
          <input className="input" placeholder="Max" type="number" value={form.max_price} onChange={set("max_price")} />
        </div>
      </fieldset>

      {/* Rooms */}
      <fieldset className="flex flex-col gap-1">
        <label className="label">Rooms</label>
        <div className="flex gap-2 flex-wrap">
          {ROOM_OPTIONS.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setForm((f) => ({ ...f, rooms: f.rooms === n ? "" : n }))}
              className={`px-3 py-1 rounded-full border text-sm font-medium transition-colors ${
                form.rooms === n
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-slate-700 border-slate-300 hover:border-blue-400"
              }`}
            >
              {n === 4 ? "4+" : n}
            </button>
          ))}
        </div>
      </fieldset>

      {/* Size */}
      <fieldset className="flex flex-col gap-1">
        <label className="label">Size (m²)</label>
        <div className="flex gap-2">
          <input className="input" placeholder="Min" type="number" value={form.min_size_m2} onChange={set("min_size_m2")} />
          <input className="input" placeholder="Max" type="number" value={form.max_size_m2} onChange={set("max_size_m2")} />
        </div>
      </fieldset>

      {/* Source */}
      <fieldset className="flex flex-col gap-1">
        <label className="label">Source</label>
        <div className="flex gap-2">
          {SOURCES.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              onClick={() => setForm((f) => ({ ...f, source: value }))}
              className={`flex-1 py-1 rounded-full border text-sm font-medium transition-colors ${
                form.source === value
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-slate-700 border-slate-300 hover:border-blue-400"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      <button
        type="submit"
        disabled={loading || !form.location}
        className="mt-2 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? "Searching…" : "Search & Scrape"}
      </button>
    </form>
  );
}

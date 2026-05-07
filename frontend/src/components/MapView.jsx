import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Circle, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function FlyToCity({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, 13, { duration: 1.2 });
  }, [center, map]);
  return null;
}

function markerColor(source) {
  return source === "facebook" ? "#1877f2" : "#7c3aed";
}

export default function MapView({ listings, center, radiusKm, highlightedId, onMarkerClick }) {
  const mapListings = listings.filter((l) => l.lat != null && l.lng != null);

  return (
    <MapContainer
      center={center ?? [48.8566, 2.3522]}
      zoom={12}
      className="w-full h-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {center && <FlyToCity center={center} />}
      {center && radiusKm && (
        <Circle
          center={center}
          radius={radiusKm * 1000}
          pathOptions={{ color: "#3b82f6", fillColor: "#3b82f6", fillOpacity: 0.06, weight: 1.5 }}
        />
      )}
      {mapListings.map((l) => (
        <CircleMarker
          key={l.id}
          center={[l.lat, l.lng]}
          radius={highlightedId === l.id ? 14 : 10}
          pathOptions={{
            fillColor: markerColor(l.source),
            fillOpacity: 0.9,
            color: "#fff",
            weight: 2,
          }}
          eventHandlers={{ click: () => onMarkerClick(l) }}
        >
          <Popup>
            <div style={{ minWidth: 180 }}>
              <p style={{ fontWeight: 600, marginBottom: 4 }}>{l.title}</p>
              {l.price != null && (
                <p style={{ color: "#2563eb", fontWeight: 700, marginBottom: 4 }}>
                  {l.currency === "EUR" ? "€" : l.currency === "GBP" ? "£" : "$"}
                  {l.price.toLocaleString()} / mo
                </p>
              )}
              <div style={{ color: "#64748b", fontSize: 12, marginBottom: 6 }}>
                {l.rooms != null && <span>{l.rooms} br&nbsp;&nbsp;</span>}
                {l.size_m2 != null && <span>{l.size_m2} m²</span>}
              </div>
              <a
                href={l.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "#3b82f6", fontSize: 13 }}
              >
                View listing →
              </a>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

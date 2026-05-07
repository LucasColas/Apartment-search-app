const SOURCE_BADGE = {
  craigslist: "bg-purple-100 text-purple-700",
  facebook: "bg-blue-100 text-blue-700",
};

export default function ListingCard({ listing, highlighted, onClick }) {
  const { title, price, currency, rooms, size_m2, address, url, image_url, source } = listing;

  return (
    <div
      onClick={onClick}
      className={`flex gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
        highlighted
          ? "border-blue-500 bg-blue-50"
          : "border-slate-200 bg-white hover:border-blue-300"
      }`}
    >
      <div className="w-20 h-20 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0">
        {image_url ? (
          <img src={image_url} alt={title} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-400 text-2xl">🏠</div>
        )}
      </div>

      <div className="flex flex-col gap-1 min-w-0">
        <p className="font-semibold text-slate-800 text-sm truncate">{title || "No title"}</p>

        {price != null && (
          <p className="text-blue-600 font-bold text-sm">
            {currency === "EUR" ? "€" : currency === "GBP" ? "£" : "$"}
            {price.toLocaleString()} / mo
          </p>
        )}

        <div className="flex gap-2 text-xs text-slate-500">
          {rooms != null && <span>{rooms} br</span>}
          {size_m2 != null && <span>{size_m2} m²</span>}
        </div>

        {address && <p className="text-xs text-slate-400 truncate">{address}</p>}

        <div className="flex items-center gap-2 mt-auto">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SOURCE_BADGE[source] ?? "bg-slate-100 text-slate-600"}`}>
            {source}
          </span>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-xs text-blue-500 hover:underline"
          >
            View →
          </a>
        </div>
      </div>
    </div>
  );
}

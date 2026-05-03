import ListingCard from "./ListingCard";

export default function ListingsList({ listings, highlightedId, onSelect }) {
  if (listings.length === 0) {
    return (
      <p className="p-4 text-sm text-slate-400 text-center">
        No listings yet. Search above to start.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2 p-3 overflow-y-auto">
      <p className="text-xs text-slate-400 font-medium px-1">{listings.length} listing{listings.length !== 1 ? "s" : ""}</p>
      {listings.map((l) => (
        <ListingCard
          key={l.id}
          listing={l}
          highlighted={l.id === highlightedId}
          onClick={() => onSelect(l)}
        />
      ))}
    </div>
  );
}

import { useState } from "react";
import { searchPlate } from "../api";

export default function PlateSearch({ onRoute, route = [] }) {
  const [plate, setPlate] = useState("");
  const [count, setCount] = useState(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    if (!plate.trim()) return;
    setLoading(true);
    try {
      const data = await searchPlate(plate.trim());
      setCount(data.length);
      onRoute?.(data);                 // App builds the ordered route from these
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="search-row">
        <input
          value={plate}
          onChange={(e) => setPlate(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="e.g. MD7078644"
        />
        <button onClick={run} disabled={loading}>{loading ? "…" : "Track"}</button>
      </div>

      {count !== null && (
        <p className="muted">
          {count} sightings · route across {route.length} camera(s)
        </p>
      )}

      {route.length > 0 && (
        <ol className="route-list">
          {route.map((s) => (
            <li key={s.order}>
              <b>{s.camera_code}</b> · {new Date(s.time).toLocaleTimeString()}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
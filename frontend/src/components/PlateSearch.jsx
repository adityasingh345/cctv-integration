import { useState } from "react";

export default function PlateSearch({ onTrack, route = [] }) {
  const [plate, setPlate] = useState("");

  function run() {
    if (!plate.trim()) return;
    onTrack?.(plate.trim());
  }

  return (
    <div>
      <div className="search-row">
        <input value={plate} onChange={(e) => setPlate(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="e.g. MD7078644" />
        <button onClick={run}>Track</button>
      </div>
      {route.length > 0 && (
        <>
          <p className="muted">Live route · {route.length} camera stop(s)</p>
          <ol className="route-list">
            {route.map((s) => (
              <li key={s.order}><b>{s.camera_code}</b> · {new Date(s.time).toLocaleTimeString()}</li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
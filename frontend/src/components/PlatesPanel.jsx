import { useEffect, useState } from "react";
import { getPlates } from "../api";

export default function PlatesPanel({ onTrack }) {
  const [plates, setPlates] = useState([]);
  useEffect(() => {
    const load = () => getPlates(30).then(setPlates).catch(() => {});
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  if (!plates.length)
    return <p className="muted">No plates read yet (depends on footage quality)…</p>;

  return (
    <ul className="alert-list">
      {plates.map((d) => (
        <li key={d.id} className="alert det-row"
            onClick={() => onTrack?.(d.plate_number)}
            title="click to track on map">
          <div className="alert-plate">🚗 {d.plate_number}</div>
          <div className="alert-meta">cam {d.camera_id} · conf {d.confidence?.toFixed(2)}</div>
          <div className="alert-time">{new Date(d.detected_at).toLocaleTimeString()}</div>
        </li>
      ))}
    </ul>
  );
}
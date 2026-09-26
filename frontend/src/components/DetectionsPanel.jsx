import { useEffect, useState } from "react";
import { getDetections } from "../api";

export default function DetectionsPanel({ onTrack }) {
  const [dets, setDets] = useState([]);
  useEffect(() => {
    const load = () => getDetections(50).then(setDets).catch(console.error);
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);
  return (
    <ul className="alert-list">
      {dets.map((d) => (
        <li key={d.id} className="alert det-row"
            onClick={() => d.plate_number && onTrack?.(d.plate_number)}
            title="click to track on map">
          <div className="alert-plate">{d.plate_number || "—"}</div>
          <div className="alert-meta">cam {d.camera_id} · conf {d.confidence?.toFixed(2)}</div>
          <div className="alert-time">{new Date(d.detected_at).toLocaleTimeString()}</div>
        </li>
      ))}
    </ul>
  );
}
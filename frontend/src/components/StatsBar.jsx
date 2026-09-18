import { useEffect, useState } from "react";
import { getStats } from "../api";

function Stat({ label, value }) {
  return <span className="stat"><b>{value ?? "–"}</b> {label}</span>;
}

export default function StatsBar({ wsConnected }) {
  const [s, setS] = useState(null);
  useEffect(() => {
    const load = () => getStats().then(setS).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="stats">
      <Stat label="cameras" value={s?.cameras} />
      <Stat label="detections" value={s?.detections} />
      <Stat label="alerts" value={s?.alerts} />
      <Stat label="watchlist" value={s?.watchlist} />
      <span className={`ws-dot ${wsConnected ? "on" : "off"}`}>
        {wsConnected ? "● live" : "○ reconnecting"}
      </span>
    </div>
  );
}
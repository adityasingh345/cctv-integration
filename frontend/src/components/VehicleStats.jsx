import { useEffect, useState } from "react";
import { getVehicleSummary, getVehicleRate } from "../api";

export default function VehicleStats() {
  const [sum, setSum] = useState(null);
  const [rate, setRate] = useState(null);

  useEffect(() => {
    const load = () => {
      getVehicleSummary().then(setSum).catch(() => {});
      getVehicleRate().then(setRate).catch(() => {});
    };
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  if (!sum) return <p className="muted">Loading vehicle analytics…</p>;
  const maxType = Math.max(1, ...Object.values(sum.by_type || {}));

  return (
    <div className="veh-stats">
      <div className="veh-top">
        <div className="veh-metric"><b>{sum.total_vehicles}</b><span>total vehicles</span></div>
        <div className="veh-metric"><b>{rate?.avg_per_minute ?? "–"}</b><span>avg / min</span></div>
        <div className="veh-metric"><b>{rate?.latest_minute_count ?? "–"}</b><span>this minute</span></div>
      </div>

      <div className="veh-section">By vehicle type</div>
      {Object.entries(sum.by_type || {}).map(([type, count]) => (
        <div key={type} className="veh-bar-row">
          <span className="veh-label">{type}</span>
          <div className="veh-bar"><div style={{ width: `${(count / maxType) * 100}%` }} /></div>
          <span className="veh-count">{count}</span>
        </div>
      ))}

      <div className="veh-section">By camera</div>
      {Object.entries(sum.by_camera || {}).map(([cam, count]) => (
        <div key={cam} className="veh-cam-row"><span>{cam}</span><b>{count}</b></div>
      ))}
    </div>
  );
}
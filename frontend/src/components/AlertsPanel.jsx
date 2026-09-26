import { useEffect, useState } from "react";
import { getAlertHistory } from "../api";

export default function AlertsPanel({ alerts, onAck, onClear, onTrack, trackedPlate }) {
  const [mode, setMode] = useState("live");      // "live" | "history"
  const [history, setHistory] = useState([]);
  const [query, setQuery] = useState("");

  // load history when switching to History mode (and refresh it periodically)
  useEffect(() => {
    if (mode !== "history") return;
    const load = () => getAlertHistory(200).then(setHistory).catch(() => {});
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [mode]);

  const source = mode === "live" ? alerts : history;
  const shown = query.trim()
    ? source.filter((a) => (a.plate_number || "").includes(query.trim().toUpperCase()))
    : source;

  return (
    <div className="alerts-wrap">
      <div className="alert-toolbar">
        <div className="mode-toggle">
          <button className={mode === "live" ? "on" : ""} onClick={() => setMode("live")}>Live</button>
          <button className={mode === "history" ? "on" : ""} onClick={() => setMode("history")}>History</button>
        </div>
        {mode === "history" && (
          <input className="alert-search" placeholder="search plate…"
            value={query} onChange={(e) => setQuery(e.target.value)} />
        )}
        {mode === "live" && alerts.length > 0 && (
          <button className="clear-btn" onClick={onClear}>Clear all</button>
        )}
      </div>

      {shown.length === 0 ? (
        <p className="muted">
          {mode === "live" ? "No alerts yet. Waiting for matches…" : "No matching alerts in history."}
        </p>
      ) : (
        <ul className="alert-list">
          {shown.map((a, i) => (
            <li key={a.id ?? i}
                className={`alert sev-${(a.severity || "med").toLowerCase()} ${a.plate_number === trackedPlate ? "tracked" : ""}`}>
              <div className="alert-plate">🚨 {a.plate_number}</div>
              <div className="alert-meta">{a.reason || "match"} · {a.camera_code || `cam ${a.camera_id}`}</div>
              {a.created_at && <div className="alert-time">{new Date(a.created_at).toLocaleString()}</div>}
              <div className="alert-actions">
                {onTrack && (
                  <button className="track-btn" onClick={() => onTrack(a.plate_number)}>
                    {a.plate_number === trackedPlate ? "Tracking" : "Track on map"}
                  </button>
                )}
                {mode === "live" && a.id != null && onAck && (
                  <button className="ack-btn" onClick={() => onAck(a.id)}>Acknowledge</button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
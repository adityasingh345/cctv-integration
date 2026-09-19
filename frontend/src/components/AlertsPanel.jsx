export default function AlertsPanel({ alerts, onAck, onClear, onTrack, trackedPlate }) {
  return (
    <div className="alerts-wrap">
      {alerts.length > 0 && <button className="clear-btn" onClick={onClear}>Clear all</button>}
      {alerts.length === 0 ? (
        <p className="muted">No alerts yet. Waiting for matches…</p>
      ) : (
        <ul className="alert-list">
          {alerts.map((a, i) => (
            <li key={a.id ?? i}
                className={`alert sev-${(a.severity || "med").toLowerCase()} ${a.plate_number === trackedPlate ? "tracked" : ""}`}>
              <div className="alert-plate">🚨 {a.plate_number}</div>
              <div className="alert-meta">{a.reason || "match"} · {a.camera_code || `cam ${a.camera_id}`}</div>
              {a.created_at && <div className="alert-time">{new Date(a.created_at).toLocaleTimeString()}</div>}
              <div className="alert-actions">
                {onTrack && (
                  <button className="track-btn" onClick={() => onTrack(a.plate_number)}>
                    {a.plate_number === trackedPlate ? "Tracking" : "Track on map"}
                  </button>
                )}
                {a.id != null && onAck && (
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
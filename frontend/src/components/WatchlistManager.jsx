import { useEffect, useState } from "react";
import { getWatchlist, addWatchlist, deleteWatchlist } from "../api";

export default function WatchlistManager() {
  const [list, setList] = useState([]);
  const [plate, setPlate] = useState("");
  const [reason, setReason] = useState("stolen");
  const [severity, setSeverity] = useState("high");
  const [err, setErr] = useState("");

  const load = () => getWatchlist().then(setList).catch(console.error);
  useEffect(() => { load(); }, []);

  async function add() {
    if (!plate.trim()) { setErr("Enter a plate"); return; }
    try {
      await addWatchlist({ plate_number: plate.trim(), reason, severity });
      setPlate(""); setErr(""); load();
    } catch {
      setErr("Add failed (already on list?)");
    }
  }
  async function remove(id) { await deleteWatchlist(id); load(); }

  return (
    <div>
      <div className="wl-form">
        <input
          value={plate}
          onChange={(e) => { setPlate(e.target.value); setErr(""); }}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="Plate e.g. MH12AB1234"
        />
        <select value={reason} onChange={(e) => setReason(e.target.value)}>
          <option>stolen</option><option>wanted</option>
          <option>suspect</option><option>blacklisted</option>
        </select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option>high</option><option>medium</option><option>low</option>
        </select>
        <button onClick={add}>Add</button>
      </div>
      {err && <p className="wl-err">{err}</p>}
      <ul className="wl-list">
        {list.map((w) => (
          <li key={w.id}>
            <span><b>{w.plate_number}</b> · {w.reason} ({w.severity})</span>
            <button className="wl-del" onClick={() => remove(w.id)} aria-label="remove">✕</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
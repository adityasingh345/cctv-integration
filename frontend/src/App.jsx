import { useEffect, useState, useRef } from "react";
import { getCameras, getAlerts, searchPlate, ackAlert as ackAlertApi, WS } from "./api";
import MapView from "./components/MapView";
import VideoGrid from "./components/VideoGrid";
import AlertsPanel from "./components/AlertsPanel";
import PlateSearch from "./components/PlateSearch";
import DetectionsPanel from "./components/DetectionsPanel";
import WatchlistManager from "./components/WatchlistManager";
import StatsBar from "./components/StatsBar";

export default function App() {
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [route, setRoute] = useState([]);
  const [trackedPlate, setTrackedPlate] = useState(null);   // live-tracked vehicle
  const [autoTrack, setAutoTrack] = useState(true);         // auto-follow newest alert
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    getCameras().then(setCameras).catch(console.error);
    getAlerts().then(setAlerts).catch(console.error);
  }, []);

  useEffect(() => {
    let stop = false;
    function connect() {
      const ws = new WebSocket(WS);
      wsRef.current = ws;
      ws.onopen = () => setWsConnected(true);
      ws.onmessage = (e) => {
        try {
          const alert = JSON.parse(e.data);
          setAlerts((prev) => [alert, ...prev].slice(0, 100));
          if (autoTrack && alert.plate_number) setTrackedPlate(alert.plate_number);
        } catch {}
      };
      ws.onclose = () => { setWsConnected(false); if (!stop) setTimeout(connect, 2000); };
    }
    connect();
    return () => { stop = true; wsRef.current?.close(); };
  }, [autoTrack]);

  function buildRoute(detections) {
    const byId = Object.fromEntries(cameras.map((c) => [c.id, c]));
    const stops = detections
      .filter((d) => byId[d.camera_id])
      .map((d) => ({
        lat: byId[d.camera_id].latitude,
        lng: byId[d.camera_id].longitude,
        camera_code: byId[d.camera_id].camera_code,
        camera_id: d.camera_id,
        time: d.detected_at,
      }))
      .sort((a, b) => new Date(a.time) - new Date(b.time));
    const r = [];
    for (const s of stops) {
      if (!r.length || r[r.length - 1].camera_id !== s.camera_id) r.push(s);
    }
    r.forEach((s, i) => (s.order = i + 1));
    setRoute(r);
  }

  // LIVE TRACKING: while a plate is tracked, poll its detections and redraw.
  useEffect(() => {
    if (!trackedPlate || !cameras.length) { setRoute([]); return; }
    let stop = false;
    async function poll() {
      try {
        const data = await searchPlate(trackedPlate);
        if (!stop) buildRoute(data);
      } catch {}
    }
    poll();
    const t = setInterval(poll, 3000);
    return () => { stop = true; clearInterval(t); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trackedPlate, cameras]);

  async function handleAck(id) {
    try { await ackAlertApi(id); } catch {}
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }
  function handleClear() { setAlerts([]); }

  return (
    <div className="app">
      <header className="topbar">
        <h1>CCTV Command Dashboard</h1>
        <StatsBar wsConnected={wsConnected} />
      </header>

      <div className="grid">
        <section className="panel map-panel">
          <h2>
            GIS Map
            {trackedPlate && (
              <span className="tracking">
                · tracking <b>{trackedPlate}</b> ({route.length} stop{route.length !== 1 ? "s" : ""})
                <button className="track-stop" onClick={() => setTrackedPlate(null)}>stop</button>
              </span>
            )}
          </h2>
          <MapView cameras={cameras} alerts={alerts} route={route} />
        </section>

        <section className="panel alerts-panel">
          <h2>
            Live Alerts
            <label className="auto-track">
              <input type="checkbox" checked={autoTrack}
                onChange={(e) => setAutoTrack(e.target.checked)} />
              auto-track
            </label>
          </h2>
          <AlertsPanel alerts={alerts} onAck={handleAck} onClear={handleClear}
            onTrack={setTrackedPlate} trackedPlate={trackedPlate} />
        </section>

        <section className="panel video-panel">
          <h2>Live Feeds</h2>
          <VideoGrid cameras={cameras} />
        </section>

        <section className="panel search-panel">
          <h2>Track a Vehicle</h2>
          <PlateSearch onTrack={setTrackedPlate} route={route} />
        </section>

        <section className="panel detections-panel">
          <h2>All Detections (live)</h2>
          <DetectionsPanel onTrack={setTrackedPlate} />
        </section>

        <section className="panel watchlist-panel">
          <h2>Watchlist Manager</h2>
          <WatchlistManager />
        </section>
      </div>
    </div>
  );
}
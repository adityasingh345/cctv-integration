import { MapContainer, TileLayer, Marker, Popup, CircleMarker, Polyline, Tooltip, useMap } from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function FitRoute({ route }) {
  const map = useMap();
  useEffect(() => {
    if (route.length > 1) {
      map.fitBounds(route.map((s) => [s.lat, s.lng]), { padding: [50, 50] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [route.length]);
  return null;
}

export default function MapView({ cameras, alerts, route = [] }) {
  const center = cameras.length
    ? [cameras[0].latitude, cameras[0].longitude]
    : [26.4499, 80.3319];

  const last = route.length ? route[route.length - 1] : null;

  return (
    <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />

      {cameras.map((c) => (
        <CircleMarker
          key={c.id}
          center={[c.latitude, c.longitude]}
          radius={8}
          pathOptions={{
            color: c.status === "online" ? "#22c55e" : "#ef4444",
            fillColor: c.status === "online" ? "#22c55e" : "#ef4444",
            fillOpacity: 0.7,
          }}
        >
          <Popup>
            <b>{c.camera_code}</b><br />
            {c.name}<br />
            Status: {c.status === "online" ? "🟢 Online" : "🔴 Offline"}<br />
            {c.department} · {c.camera_type}
          </Popup>
        </CircleMarker>
      ))}

      {route.length > 0 && (
        <>
          <Polyline positions={route.map((s) => [s.lat, s.lng])}
            pathOptions={{ color: "#2563eb", weight: 4, opacity: 0.8, dashArray: "8 6" }} />
          {route.map((s) => (
            <CircleMarker key={`rt-${s.order}`} center={[s.lat, s.lng]}
              radius={14} pathOptions={{ color: "#2563eb", fillColor: "#2563eb", fillOpacity: 0.85 }}>
              <Tooltip permanent direction="center" className="route-num">{s.order}</Tooltip>
              <Popup>Stop {s.order}: <b>{s.camera_code}</b><br />{new Date(s.time).toLocaleString()}</Popup>
            </CircleMarker>
          ))}
          {last && (
            <CircleMarker center={[last.lat, last.lng]} radius={20}
              pathOptions={{ color: "#22c55e", weight: 3, fillColor: "#22c55e", fillOpacity: 0.15 }}>
              <Popup>Last seen: <b>{last.camera_code}</b><br />{new Date(last.time).toLocaleString()}</Popup>
            </CircleMarker>
          )}
          <FitRoute route={route} />
        </>
      )}
    </MapContainer>
  );
}
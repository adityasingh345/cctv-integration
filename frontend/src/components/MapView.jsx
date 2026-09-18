import { MapContainer, TileLayer, Marker, Popup, CircleMarker, Polyline, Tooltip, useMap } from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Zoom/pan the map to fit the route whenever it changes.
function FitRoute({ route }) {
  const map = useMap();
  useEffect(() => {
    if (route.length > 1) {
      map.fitBounds(route.map((s) => [s.lat, s.lng]), { padding: [40, 40] });
    }
  }, [route, map]);
  return null;
}

export default function MapView({ cameras, alerts, route = [] }) {
  const center = cameras.length
    ? [cameras[0].latitude, cameras[0].longitude]
    : [26.4499, 80.3319];

  return (
    <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />

      {/* camera markers */}
      {cameras.map((c) => (
        <Marker key={c.id} position={[c.latitude, c.longitude]}>
          <Popup>
            <b>{c.camera_code}</b><br />{c.name}<br />
            {c.department} · {c.camera_type}
          </Popup>
        </Marker>
      ))}

      {/* alert pins */}
      {alerts
        .filter((a) => a.latitude && a.longitude)
        .slice(0, 30)
        .map((a, i) => (
          <CircleMarker key={`al-${a.id ?? i}`} center={[a.latitude, a.longitude]}
            radius={12} pathOptions={{ color: "red", fillColor: "red", fillOpacity: 0.5 }}>
            <Popup>🚨 <b>{a.plate_number}</b><br />{a.reason} ({a.severity})<br />{a.camera_code}</Popup>
          </CircleMarker>
        ))}

      {/* ---- VEHICLE ROUTE: line + numbered stops in time order ---- */}
      {route.length > 0 && (
        <>
          <Polyline
            positions={route.map((s) => [s.lat, s.lng])}
            pathOptions={{ color: "#2563eb", weight: 4, opacity: 0.8, dashArray: "8 6" }}
          />
          {route.map((s) => (
            <CircleMarker key={`rt-${s.order}`} center={[s.lat, s.lng]}
              radius={14} pathOptions={{ color: "#2563eb", fillColor: "#2563eb", fillOpacity: 0.85 }}>
              <Tooltip permanent direction="center" className="route-num">{s.order}</Tooltip>
              <Popup>
                Stop {s.order}: <b>{s.camera_code}</b><br />
                {new Date(s.time).toLocaleString()}
              </Popup>
            </CircleMarker>
          ))}
          <FitRoute route={route} />
        </>
      )}
    </MapContainer>
  );
}
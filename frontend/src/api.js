export const API = "http://localhost:8000";
export const HLS = "http://localhost:8888";
export const WS  = "ws://localhost:8000/ws/alerts";

export async function getCameras() {
  return (await fetch(`${API}/cameras`)).json();
}
export async function getAlerts() {
  return (await fetch(`${API}/alerts`)).json();
}
export async function searchPlate(plate) {
  return (await fetch(`${API}/detections?plate=${encodeURIComponent(plate)}&limit=200`)).json();
}
export async function getDetections(limit = 50) {
  return (await fetch(`${API}/detections?limit=${limit}`)).json();
}
export async function getStats() {
  return (await fetch(`${API}/stats`)).json();
}
export async function getWatchlist() {
  return (await fetch(`${API}/watchlist`)).json();
}
export async function addWatchlist(entry) {
  const r = await fetch(`${API}/watchlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
export async function deleteWatchlist(id) {
  await fetch(`${API}/watchlist/${id}`, { method: "DELETE" });
}
export async function ackAlert(id) {
  await fetch(`${API}/alerts/${id}/ack`, { method: "PATCH" });
}
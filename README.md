# CCTV Integration Platform (Model 1 + Model 2 Hybrid)

Onboard heterogeneous CCTV cameras, run live AI analytics (vehicle detection +
ANPR), match plates against a watchlist, raise real-time alerts, and trace a
vehicle's route on a GIS map.

- **Model 1** — camera registry + GIS map (this repo's `cameras` table + map view)
- **Model 2** — unified live viewing + ANPR analytics + alerting

## Architecture (runtime pipeline)

```
Camera RTSP  ->  MediaMTX (HLS)  ->  Analytics (YOLO + ANPR)  ->  PostgreSQL/PostGIS  ->  Dashboard
                                                                    |  watchlist match  |
                                                                    +--> alerts --(WS)--+
```

`camera_id` is the glue: created in the registry, stamped on every detection,
used by the dashboard to place detections and alerts on the map.

## Tech stack
- Backend: FastAPI (Python)
- DB: PostgreSQL + PostGIS
- Media: MediaMTX (RTSP -> HLS)
- AI: YOLOv8 (detection) + fast-plate-ocr / PaddleOCR (ANPR)
- Alert bus: Redis pub/sub -> WebSocket
- Frontend: React (Vite) + Leaflet
- Orchestration: Docker Compose

## Build roadmap

| Phase | What we build | Status |
|-------|---------------|--------|
| 1 | Project scaffold: folders, docker-compose, DB schema, sample data | DONE |
| 2 | Registry backend (Model 1): camera CRUD, bulk CSV upload, watchlist API | next |
| 3 | Ingestion: MediaMTX config + simulate ~50 cameras from video via FFmpeg | |
| 4 | Analytics worker: YOLO detection + ANPR, write detections to DB | |
| 5 | Watchlist matching + real-time alerts (Redis -> WebSocket) | |
| 6 | Frontend dashboard: GIS map, live video grid, alerts panel | |
| 7 | Plate search + vehicle route reconstruction on the map | |
| 8 | Polish: dockerise fully, sample gap-analysis report, scale write-up | |

## Getting started (after Phase 2+)

```bash
cp .env.example .env      # then edit secrets
docker compose up --build
# backend  -> http://localhost:8000/docs
# frontend -> http://localhost:5173
```

## Folder layout

```
cctv-integration/
├── docker-compose.yml
├── .env.example
├── db/
│   └── init.sql            # schema (auto-runs on first DB start)
├── data/
│   ├── sample_cameras.csv
│   └── sample_watchlist.csv
├── backend/               # FastAPI app  (Phase 2, 5)
│   └── app/{models,schemas,routers,ws}
├── ingestion/             # MediaMTX + camera simulator (Phase 3)
├── analytics/             # YOLO + ANPR worker (Phase 4)
└── frontend/              # React + Leaflet dashboard (Phase 6, 7)
```

# CCTV Integration & AI Analytics Platform

A statewide-style CCTV integration platform that onboards heterogeneous cameras,
runs live AI video analytics (vehicle detection, classification, and ANPR),
cross-references number plates against a watchlist, raises real-time alerts,
traces vehicles across cameras on a GIS map, and federates multiple vendor VMS
platforms — all from a single web command dashboard.

Built as a **Model 1 + Model 2 + Model 3 hybrid** with a documented **Model 4**
(Central VMS) scale-up design.

---

## Table of contents
1. [What it does](#what-it-does)
2. [Architecture](#architecture)
3. [Tech stack](#tech-stack)
4. [Project structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Quick start](#quick-start)
7. [Feature walkthrough](#feature-walkthrough)
8. [Real camera integration](#real-camera-integration)
9. [Model 3 — VMS federation](#model-3--vms-federation)
10. [Configuration](#configuration)
11. [API reference](#api-reference)
12. [Robustness & production hardening](#robustness--production-hardening)
13. [Known limitations](#known-limitations)
14. [Roadmap](#roadmap)

---

## What it does

The platform ingests camera feeds (live RTSP or recorded clips), analyses each
frame with AI, and turns raw video into structured, searchable intelligence:

- **Camera registry & GIS** — onboard cameras (manual or bulk CSV), each with a
  location shown on an interactive map, with live online/offline status.
- **Live viewing** — all camera feeds shown in a video grid in the browser.
- **Vehicle analytics** — YOLOv8 detects and classifies every vehicle
  (car / truck / bus / motorcycle); the dashboard shows totals, per-type
  breakdown, per-camera counts, and a live per-minute traffic rate.
- **ANPR** — reads number plates when footage quality allows (plate-detector +
  OCR), with a regex filter for plate-shaped results.
- **Watchlist matching & alerts** — every detected plate is fuzzy-matched
  against a watchlist; matches raise real-time alerts pushed over WebSocket.
- **Vehicle tracking** — search a plate (or auto-track an alert) to draw its
  route across cameras in time order on the GIS map.
- **Historical alerts** — browse and search all past alerts.
- **VMS federation (Model 3)** — connect heterogeneous vendor VMS platforms
  through per-vendor adapters into one unified stream.

**Graceful degradation:** vehicle type, count and GIS metadata are extracted from
*any* footage; ANPR and watchlist alerting activate when footage quality permits.
Analytics scale to the available signal rather than failing on poor video.

---

## Architecture

```
 Camera sources          Media hub            AI analytics           Backend + data          Presentation
 ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────┐
 │ Live RTSP    │──▶│  MediaMTX    │──▶│  Analytics worker │──▶│  FastAPI backend │──▶│  React +     │
 │ + video clips│   │ RTSP → HLS   │   │  YOLOv8 + ANPR    │   │  PostgreSQL/     │   │  Leaflet     │
 └──────────────┘   └──────────────┘   └──────────────────┘   │  PostGIS + Redis │   │  dashboard   │
                          │  HLS ────────────────────────────────────────────────────▶│  (video grid)│
                          └───────────────────────────────────────────────────────────└──────────────┘

 Model 3 federation (added, non-invasive):
   Mock VMS A ─┐
               ├─▶ per-vendor adapters ─▶ federation middleware ─▶ POST /detections/ingest (existing API)
   Mock VMS B ─┘
```

**Data flow:** camera feeds are pulled by MediaMTX (which handles RTSP auth) and
re-served as HLS (for the browser) and clean RTSP (for analytics). The analytics
worker samples frames, runs YOLO + ANPR, and POSTs detections to the backend.
The backend stores them in PostgreSQL/PostGIS with camera location and timestamp,
matches plates against the watchlist, publishes alerts through Redis, and relays
them to the dashboard over WebSocket. `camera_id` is the join key that ties every
detection and alert back to a map location.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python) |
| Database | PostgreSQL + PostGIS |
| Media server | MediaMTX (RTSP ⇄ HLS) |
| AI — detection | YOLOv8 (Ultralytics) |
| AI — ANPR/OCR | license-plate detector + EasyOCR |
| Alert bus | Redis pub/sub → WebSocket |
| Frontend | React (Vite) + Leaflet |
| Federation | FastAPI mock VMS + per-vendor adapters |
| Orchestration | Docker Compose |

---

## Project structure

```
cctv-integration/
├── docker-compose.yml               # all services, one command
├── docker-compose.federation.yml    # Model 3 mock VMS + middleware
├── .env                             # configuration (see below)
├── db/
│   └── init.sql                     # schema: cameras, detections, watchlist, alerts (+ PostGIS)
├── data/
│   ├── sample_cameras.csv           # sample camera registry
│   └── sample_watchlist.csv         # sample watchlist plates
├── backend/                         # FastAPI application
│   ├── Dockerfile
│   └── app/
│       ├── main.py                  # app + startup tasks (health, retention, alert bridge)
│       ├── config.py, database.py
│       ├── models/                  # SQLAlchemy models
│       ├── schemas/                 # Pydantic schemas
│       ├── routers/                 # cameras, watchlist, detections, alerts, stats, analytics
│       ├── matching.py              # fuzzy plate matching (configurable threshold)
│       └── ws/manager.py            # WebSocket connection manager
├── analytics/                       # AI worker
│   ├── Dockerfile
│   ├── worker.py                    # per-camera threads, sampling, rate-control, fault isolation
│   ├── detector.py                  # YOLOv8 vehicle detection
│   └── anpr.py                      # plate detection + OCR
├── ingestion/
│   ├── mediamtx.yml                 # media server config
│   └── simulate_cameras.py          # stream clips as RTSP camera feeds
├── federation/                      # Model 3
│   ├── mock_vms_a/ , mock_vms_b/    # two vendor VMS with different APIs
│   ├── adapters/                    # per-vendor normalisers + camera map
│   └── middleware.py                # polls, normalises, correlates, forwards
└── frontend/                        # React dashboard
    ├── Dockerfile
    └── src/
        ├── App.jsx                  # state, WebSocket, live tracking
        ├── api.js                   # all backend endpoints
        └── components/              # MapView, VideoGrid, AlertsPanel, PlateSearch,
                                     # DetectionsPanel, VehicleStats, WatchlistManager, StatsBar
```

---

## Prerequisites

- **Docker** + **Docker Compose**
- **FFmpeg** on the host (for the camera simulator): `sudo dnf install ffmpeg` / `apt install ffmpeg`
- A few **video clips** in `clips/` (traffic footage) — used as simulated camera feeds
- ~5 GB free disk (the AI image bundles PyTorch)

---

## Quick start

```bash
# 1. configure
cp .env.example .env          # then review values

# 2. start the whole stack (one command)
docker compose up -d

# 3. onboard the sample cameras
curl -F "file=@data/sample_cameras.csv" http://localhost:8000/cameras/bulk-upload

# 4. stream clips as camera feeds (separate terminal, leave running)
python ingestion/simulate_cameras.py --videos ./clips --count 5

# 5. open the dashboard
#    http://localhost:5173
#    API docs: http://localhost:8000/docs
```

Recommended start order if bringing services up individually:
`db → redis → mediamtx → backend → analytics → frontend`.

**Stop everything:** `docker compose down` (data persists in the DB volume).

---

## Feature walkthrough

**Onboarding & registry** — add cameras via the API/CSV; each appears on the GIS
map with a marker coloured by live status (green = online, red = offline).

**Live feeds** — the video grid plays each camera's HLS stream in the browser.

**Vehicle analytics** — the analytics panel shows total vehicles, a per-type bar
breakdown (car/truck/bus/motorcycle), per-camera counts, and a live avg-per-minute
and this-minute traffic rate.

**Detected plates** — a dedicated panel lists plate reads (when footage allows),
clickable to trace the vehicle on the map.

**Watchlist manager** — add/remove watchlist plates (with reason + severity)
directly from the dashboard.

**Live alerts** — when a detected plate matches the watchlist, an alert appears
in real time; each alert can be acknowledged, and (with auto-track on) the map
automatically draws that vehicle's route.

**Alert history** — toggle the alerts panel to History to browse and search all
past alerts by plate.

**Vehicle tracking** — type a plate (or click an alert/detection); the map draws
the vehicle's chronological route across the cameras that saw it, with a
"last seen" marker, updating live.

---

## Real camera integration

The platform integrates live RTSP CCTV via standard protocols. MediaMTX pulls a
real camera stream (handling RTSP authentication and TCP transport), then
re-serves it locally as RTSP for analytics and HLS for the dashboard — which
resolves credential-parsing and browser CORS constraints in one place.

To add a real camera, point a MediaMTX path at its RTSP source and onboard a
registry entry whose `rtsp_url` is the local MediaMTX path (e.g.
`rtsp://mediamtx:8554/cam01`). The analytics and dashboard treat real and
simulated feeds identically.

> Note: ANPR accuracy depends on camera placement and resolution. Wide-angle or
> night PTZ feeds yield reliable *vehicle* metadata (type, count, GIS) but may not
> produce readable *plates* — plate-capture-optimised cameras are required for
> consistent ANPR, as covered in the Model 4 scale design.

---

## Model 3 — VMS federation

Added as an isolated, non-invasive layer that never modifies the core system:

- **Two mock VMS services** expose deliberately different APIs (different field
  names, units, and response shapes) — standing in for real vendor platforms.
- **Per-vendor adapters** normalise each vendor's format into the standard
  detection shape and map vendor camera codes to registry camera IDs.
- **Federation middleware** polls both VMS, runs the adapters, correlates
  cross-system duplicates, and forwards to the existing `/detections/ingest`.

Adding a new vendor is a new adapter file — no change to the backend, dashboard,
or analytics. Run with:

```bash
docker compose -f docker-compose.federation.yml up -d --build
```

---

## Configuration

Set in `.env`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER/PASSWORD/DB` | — | database credentials |
| `DATABASE_URL` | — | backend DB connection |
| `REDIS_URL` | `redis://redis:6379/0` | alert pub/sub |
| `MAX_CAMERAS` | `5` | how many cameras the worker processes |
| `FRAME_SAMPLE_EVERY` | `5` | analyse every Nth frame |
| `DEDUPE_WINDOW` | `3` | seconds before re-logging the same (camera, type, plate) |
| `MATCH_THRESHOLD` | `0.82` | fuzzy plate-match sensitivity (0–1) |
| `RETENTION_DAYS` | `7` | auto-delete detections older than this |
| `PLATE_MODEL` | `models/license_plate.pt` | optional plate-detector weights |

---

## API reference

Interactive docs at `http://localhost:8000/docs`.

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/cameras` | list / add cameras |
| POST | `/cameras/bulk-upload` | onboard cameras from CSV |
| GET/POST/DELETE | `/watchlist` | manage watchlist |
| POST | `/detections/ingest` | analytics posts detections here |
| GET | `/detections?plate=&limit=` | search detections |
| GET | `/alerts` | list alerts (live + history) |
| PATCH | `/alerts/{id}/ack` | acknowledge an alert |
| GET | `/analytics/summary` | totals, by type, by camera |
| GET | `/analytics/rate` | avg + latest per-minute rate |
| WS | `/ws/alerts` | live alert stream |

---

## Robustness & production hardening

Improvements made beyond the core prototype:

- **Live camera health** — a background task marks cameras online/offline based
  on recent detection activity; the map reflects it in real time.
- **Detection rate control** — a per-camera dedupe window prevents the same
  vehicle being logged every frame, cutting detection volume ~90% and keeping
  counts meaningful.
- **Automatic data retention** — a background task prunes detections older than
  `RETENTION_DAYS`, keeping the database bounded (alerts are preserved).
- **Fault isolation** — each camera runs in its own thread with per-frame
  error handling, so a corrupt frame or a single failing camera never breaks
  the pipeline for the others.
- **Configurable matching** — the fuzzy-match threshold is an env variable, not
  a hardcoded constant.
- **Fully containerised** — every service (including the frontend) starts with
  a single `docker compose up -d`.

---

## Known limitations

Stated honestly (with intended fixes in the roadmap):

- **No authentication / RBAC yet** — the API is currently open; role-based access
  and TLS are designed but not implemented. Highest-priority remaining item for a
  law-enforcement deployment.
- **ANPR accuracy is footage-bound** — poor/wide/night feeds yield vehicle
  metadata but few readable plates. This is a camera-quality constraint, handled
  by graceful degradation.
- **Counting is event-based, not unique-vehicle** — rate control deduplicates
  per-frame noise but does not yet assign persistent track IDs, so counts are
  approximate. Multi-object tracking is the upgrade path.
- **Single inference pipeline per camera** — one model chain per feed; running
  multiple models (e.g. + face recognition) per camera needs an orchestration
  layer.
- **Cameras connect directly to analytics** — a dedicated camera-management
  service between cameras and the AI is a planned architectural improvement.
- **Alert delivery is in-dashboard** — alerts are stored and pushed to the
  dashboard, but external delivery (email/SMS/webhook) is not yet implemented.

---

## Roadmap

Prioritised next steps:

1. **Authentication + RBAC + TLS** — department-wise roles, secure the API.
2. **Camera management service** — a layer handling onboarding, health,
   credentials, and load-balancing feeds before the AI tier.
3. **Multi-object tracking** — persistent IDs for accurate unique-vehicle counts,
   speed, and direction.
4. **External alert delivery** — email / webhook / push with escalation.
5. **Multi-model orchestration** — run several analytics models per feed.
6. **Government DB integrations** — VAHAN / SARTHI / AFIS connectors (adapter
   pattern), read-only and audited.
7. **Statewide scale** — GPU inference clusters, tiered storage, Kafka backbone,
   Kubernetes, regional edge — as detailed in the Model 4 Central VMS design.

---

*A hybrid CCTV integration platform: real camera integration, AI vehicle analytics
and ANPR, watchlist alerting, cross-camera GIS tracking, and vendor-VMS federation —
containerised and demo-ready.*

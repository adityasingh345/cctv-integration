-- ============================================================
-- CCTV Integration Platform - Database Schema
-- PostgreSQL + PostGIS
-- This runs automatically on first container start.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ------------------------------------------------------------
-- 1. CAMERAS  (Model 1: the registry)
--    Every camera onboarded into the platform lives here.
--    camera_id is the glue that ties detections + alerts to a location.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cameras (
    id            SERIAL PRIMARY KEY,
    camera_code   VARCHAR(64) UNIQUE NOT NULL,   -- human/dept code e.g. "TRAF-KNP-014"
    name          VARCHAR(255) NOT NULL,
    department    VARCHAR(128),                  -- Traffic, Police, Municipal...
    camera_type   VARCHAR(64),                   -- fixed / ptz / anpr ...
    rtsp_url      TEXT NOT NULL,                 -- feed source
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    geom          GEOMETRY(Point, 4326),         -- PostGIS point for map/spatial queries
    status        VARCHAR(32) DEFAULT 'unknown', -- online / offline / unknown
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Auto-fill the PostGIS geometry from lat/long on insert or update.
CREATE OR REPLACE FUNCTION set_camera_geom() RETURNS trigger AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_camera_geom ON cameras;
CREATE TRIGGER trg_camera_geom
    BEFORE INSERT OR UPDATE ON cameras
    FOR EACH ROW EXECUTE FUNCTION set_camera_geom();

-- ------------------------------------------------------------
-- 2. WATCHLIST  (stolen / wanted / blacklisted vehicles)
--    You match every detected plate against this table.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlist (
    id            SERIAL PRIMARY KEY,
    plate_number  VARCHAR(32) UNIQUE NOT NULL,   -- normalised, uppercase, no spaces
    reason        VARCHAR(128),                  -- stolen / wanted / suspect ...
    severity      VARCHAR(32) DEFAULT 'medium',  -- low / medium / high
    notes         TEXT,
    active        BOOLEAN DEFAULT true,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------
-- 3. DETECTIONS  (Model 2: every AI hit from the feeds)
--    One row per plate/vehicle the analytics worker sees.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detections (
    id            BIGSERIAL PRIMARY KEY,
    camera_id     INTEGER REFERENCES cameras(id) ON DELETE SET NULL,
    plate_number  VARCHAR(32),                   -- may be NULL for a vehicle w/o readable plate
    object_type   VARCHAR(32) DEFAULT 'vehicle', -- vehicle / person ...
    confidence    REAL,
    snapshot_path TEXT,                          -- cropped image on disk / object store
    detected_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_detections_plate ON detections(plate_number);
CREATE INDEX IF NOT EXISTS idx_detections_time  ON detections(detected_at);
CREATE INDEX IF NOT EXISTS idx_detections_cam   ON detections(camera_id);

-- ------------------------------------------------------------
-- 4. ALERTS  (a detection that matched the watchlist)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id            BIGSERIAL PRIMARY KEY,
    detection_id  BIGINT REFERENCES detections(id) ON DELETE CASCADE,
    watchlist_id  INTEGER REFERENCES watchlist(id) ON DELETE CASCADE,
    camera_id     INTEGER REFERENCES cameras(id) ON DELETE SET NULL,
    plate_number  VARCHAR(32),
    reason        VARCHAR(128),
    severity      VARCHAR(32),
    acknowledged  BOOLEAN DEFAULT false,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(created_at);

-- ------------------------------------------------------------
-- Handy view: a vehicle's full route (used by plate search).
-- Returns every detection of a plate with its camera location, in time order.
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW vehicle_route AS
SELECT d.plate_number,
       d.detected_at,
       c.camera_code,
       c.name        AS camera_name,
       c.latitude,
       c.longitude
FROM detections d
JOIN cameras c ON c.id = d.camera_id
WHERE d.plate_number IS NOT NULL
ORDER BY d.plate_number, d.detected_at;

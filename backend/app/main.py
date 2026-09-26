import asyncio
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import cameras, watchlist, detections, alerts, stats, analytics

import os 
from datetime import datetime, timezone, timedelta
from .database import SessionLocal
from .models import Camera, Detection
from sqlalchemy import func, text

from .ws.manager import manager

app = FastAPI(
    title="CCTV Integration Platform API",
    description="Model 1 + Model 2 hybrid - registry, watchlist, analytics, alerts",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)
app.include_router(watchlist.router)
app.include_router(detections.router)
app.include_router(alerts.router)
app.include_router(stats.router)
app.include_router(analytics.router)

@app.on_event("startup")
async def start_camera_health():
    WINDOW = 60
    INTERVAL = 30

    async def loop():
        while True:
            try:
                db = SessionLocal()
                active = db.execute(text(
                    "SELECT DISTINCT camera_id FROM detections "
                    "WHERE detected_at > now() - make_interval(secs => :w)"
                ), {"w": WINDOW}).fetchall()
                active_ids = {row[0] for row in active}

                for c in db.query(Camera).all():
                    new_status = "online" if c.id in active_ids else "offline"
                    if c.status != new_status:
                        c.status = new_status
                db.commit(); db.close()
            except Exception as e:
                print(f"[health] camera health check failed: {e}")
            await asyncio.sleep(INTERVAL)

    asyncio.create_task(loop())

@app.on_event("startup")
async def start_retention():
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))
    INTERVAL = 3600   # run cleanup every hour

    async def loop():
        while True:
            try:
                db = SessionLocal()
                result = db.execute(text(
                    "DELETE FROM detections WHERE detected_at < now() - make_interval(days => :d)"
                ), {"d": RETENTION_DAYS})
                db.commit(); db.close()
                if result.rowcount:
                    print(f"[retention] deleted {result.rowcount} old detections")
            except Exception as e:
                print(f"[retention] cleanup failed: {e}")
            await asyncio.sleep(INTERVAL)

    asyncio.create_task(loop())

# Bridge: subscribe to Redis "alerts" and fan out to all WebSocket clients.
@app.on_event("startup")
async def start_alert_bridge():
    async def listen():
        while True:
            try:
                r = aioredis.from_url(settings.REDIS_URL)
                pubsub = r.pubsub()
                await pubsub.subscribe("alerts")
                print("[bridge] subscribed to redis 'alerts'")
                while True:
                    msg = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if msg and msg.get("type") == "message":
                        data = msg["data"]
                        if isinstance(data, bytes):
                            data = data.decode()
                        await manager.broadcast(data)
                    await asyncio.sleep(0.01)
            except Exception as e:
                print(f"[bridge] redis listener error: {e}; retrying in 2s")
                await asyncio.sleep(2)
    asyncio.create_task(listen())

@app.on_event("startup")
async def start_retention():
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "7"))
    INTERVAL = 3600   # run cleanup hourly

    async def loop():
        while True:
            try:
                db = SessionLocal()
                db.execute(text(
                    "DELETE FROM detections WHERE detected_at < now() - make_interval(days => :d)"
                ), {"d": RETENTION_DAYS})
                db.commit(); db.close()
            except Exception as e:
                print(f"[retention] cleanup failed: {e}")
            await asyncio.sleep(INTERVAL)

    asyncio.create_task(loop())

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
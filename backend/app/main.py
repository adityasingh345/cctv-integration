import asyncio
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import cameras, watchlist, detections, alerts, stats

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

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
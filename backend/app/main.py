from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import cameras, watchlist

app = FastAPI(
    title="CCTV Integration Platform API",
    description="Model 1 + Model 2 hybrid - registry, watchlist, analytics, alerts",
    version="0.2.0",
)

# Allow the React dev server to call the API during the hackathon.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)
app.include_router(watchlist.router)

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
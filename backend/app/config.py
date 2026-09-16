import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cctv:cctv@db:5432/cctv")
    REDIS_URL    = os.getenv("REDIS_URL", "redis://redis:6379/0")
    HLS_BASE_URL = os.getenv("HLS_BASE_URL", "http://localhost:8888")

settings = Settings()
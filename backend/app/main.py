import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.ingestion.mqtt_consumer import mqtt_consumer
from app.api.v1.router import api_v1_router
from app.api.websocket import router as websocket_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    mqtt_consumer.start(loop)
    yield
    mqtt_consumer.stop()


app = FastAPI(
    title="PolarTwin Digital Twin API",
    description="Backend API for Indian Antarctic Stations (Maitri & Bharati)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)
app.include_router(websocket_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}

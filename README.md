# PolarTwin — Backend

FastAPI backend for the PolarTwin Digital Twin system for Indian Antarctic Stations (Maitri & Bharati).

## Stack
- **FastAPI** + **Uvicorn** (Python 3.11)
- **PostgreSQL** via [Supabase](https://supabase.com)
- **MQTT** broker (Eclipse Mosquitto — runs as a Docker sidecar)
- **Anthropic Claude** for AI assistant
- **scikit-learn** ML models for anomaly detection & energy forecasting

## Project Structure
```
backend/        FastAPI application source
ml/             Trained ML models + training scripts
scripts/        Utility scripts (e.g., seed.py to seed the DB)
docs/           Architecture & API documentation
docker/         Mosquitto MQTT broker config
Dockerfile      Production Docker image
docker-compose.yml  Runs backend + MQTT broker together
```

## Quick Start (Local)

```bash
# 1. Copy env file and fill in your values
cp .env.example .env

# 2. Start services
docker-compose up --build

# 3. Seed the database (first time only)
docker exec -it polartwin-backend python /app/../scripts/seed.py
```

API will be available at `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

## Environment Variables

See [`.env.example`](.env.example) for all required variables.

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `MQTT_HOST` | MQTT broker host (`mqtt` inside Docker) |
| `MQTT_PORT` | MQTT broker port (default: `1883`) |
| `ANTHROPIC_API_KEY` | Claude API key |
| `CORS_ORIGINS` | Comma-separated allowed origins (your Vercel URL) |

## Deployment

This service is deployed via Docker on a VPS/cloud host. The `docker-compose.yml` starts:
- `backend` — FastAPI on port 8000
- `mqtt` — Mosquitto broker on port 1883 (also used by the simulator)

The simulator ([`polar-twin-simulator`](https://github.com/your-org/polar-twin-simulator)) connects to this MQTT broker externally.

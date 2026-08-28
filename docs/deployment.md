# 🐳 PolarTwin — Deployment & Operations Runbook

## 🚀 Quickstart

1. Clone or navigate to the repository:
   ```bash
   cd polar-twin
   ```

2. Configure environment variables (optional, defaults provided):
   ```bash
   cp .env.example .env
   ```

3. Launch the full multi-container stack with Docker Compose:
   ```bash
   docker compose up --build
   ```

---

## 📦 Container Services & Ports

| Container Name | Service Role | Port Binding | Health Check |
|---|---|---|---|
| `polartwin-postgres` | PostgreSQL 15 Database | `5432:5432` | `pg_isready -U polartwin_user` |
| `polartwin-mqtt` | Mosquitto MQTT Broker | `1883:1883` | `mosquitto_sub -t $SYS/# -c 1` |
| `polartwin-backend` | FastAPI & Digital Twin Engine | `8000:8000` | `curl localhost:8000/health` |
| `polartwin-simulator` | Telemetry Generator | Internal | Daemon tick loop |
| `polartwin-frontend` | Next.js 14 Web Command Center | `3000:3000` | HTTP 200 on `/` |

# 🏛️ PolarTwin — System Architecture & Data Flow

PolarTwin is an intelligent digital twin platform for India's Antarctic research stations (**Maitri** & **Bharati**).

```
                      ┌────────────────────────────────────────┐
                      │    Antarctic Multi-Domain Simulator    │
                      │  (Environment, Power, Comms, Stocks)   │
                      └───────────────────┬────────────────────┘
                                          │ MQTT (Port 1883)
                                          ▼
                      ┌────────────────────────────────────────┐
                      │       Eclipse Mosquitto Broker         │
                      └───────────────────┬────────────────────┘
                                          │ Paho-MQTT Subscription
                                          ▼
                      ┌────────────────────────────────────────┐
                      │       FastAPI Ingestion Pipeline       │
                      │  (mqtt_consumer.py & ingestion_service)│
                      └───────────────────┬────────────────────┘
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
    ┌───────────────────────────┐                   ┌───────────────────────────┐
    │  PostgreSQL 15 Time-Series│                   │    Digital Twin Engine    │
    │  (Historical Archival)    │                   │   (In-Memory Live State)  │
    └───────────────────────────┘                   └─────────────┬─────────────┘
                                                                  │
              ┌───────────────────────────┬───────────────────────┴───────────────────────┐
              ▼                           ▼                                               ▼
┌───────────────────────────┐┌───────────────────────────┐                   ┌───────────────────────────┐
│     Rule Alert Engine     ││   Scikit-Learn ML Models  │                   │     WebSocket Server      │
│  (Deterministic Threshold)││ (IsolationForest / RUL)   │                   │   (/ws/stations/{id})     │
└───────────────────────────┘└───────────────────────────┘                   └─────────────┬─────────────┘
                                                                                           │ Real-Time Push
                                                                                           ▼
                                                                             ┌───────────────────────────┐
                                                                             │ Next.js 14 Web Frontend   │
                                                                             │ (3D Canvas, Hub, Alerts)  │
                                                                             └───────────────────────────┘
```

---

## 📡 MQTT Topic Hierarchy

All simulator streams follow the standard topic convention:
`stations/{station_id}/{domain}/{asset_id}/{metric}`

- `stations/maitri/environment/ambient/temperature`
- `stations/maitri/energy/generator/GEN-MAI-001/power_kw`
- `stations/maitri/energy/battery/BAT-MAI-001/soc`
- `stations/maitri/infrastructure/HVC-MAI-001/cabin_temp`
- `stations/maitri/inventory/diesel/volume_liters`

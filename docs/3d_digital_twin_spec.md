# 🧊 PolarTwin 3D Spatial Digital Twin Specification

This document outlines the architectural, mathematical, and rendering design of the 3D Digital Twin environment for India's Antarctic research stations: **Maitri** (Schirmacher Oasis) and **Bharati** (Larsemann Hills).

---

## 🏛️ Station Design & Architectural Contrast

| Dimension | Maitri Research Station | Bharati Research Station |
|---|---|---|
| **Geographical Context** | Inland rocky permafrost & moraines at Schirmacher Oasis (-70.7667° S, 11.7333° E) | Coastal rocky headland at Larsemann Hills overlooking Prydz Bay (-69.4072° S, 76.1872° E) |
| **Water Source** | Freshwater sub-ice intake from **Lake Priyadarshini** via heated polyethylene lines | Seawater subsea intake from **Prydz Bay** with Reverse Osmosis (RO) Desalination Plant |
| **Architectural Style** | 2-story modular insulated container units on steel stilts (1989 utilitarian design) | 3-story faceted aerodynamic aluminum envelope on heavy structural steel stilts (2012 bof/IMS design) |
| **Power Infrastructure** | 3x Kirloskar/Cummins 100 kW Diesel Gensets + 150 kWh LiFePO4 BESS | 2x MAN Combined Heat & Power (CHP) Units with heat recovery + 250 kWh BESS |
| **Satellite Comms** | Ku-band tracking radome + HF lattice tower (INSAT relay to NCAOR Goa) | Dual 7.3m Earth Observation tracking radomes (ISRO / NRSC remote sensing downlink) |
| **Aviation Deck** | Compacted snow perimeter helipad with approach beacons | Certified elevated octagonal structural steel helideck (12-ton rating) |

---

## 🌐 Coordinate Space & Asset Registry Mapping

All visual assets inherit typed digital twin properties defined in `frontend/lib/3d/assetRegistry.ts`:

```typescript
export interface DigitalTwinAsset {
  assetId: string;
  stationId: "maitri" | "bharati";
  name: string;
  category: "POWER" | "FUEL" | "WATER" | "HVAC" | "COMMS" | "SCIENCE" | "BUILDING" | "LOGISTICS";
  position3D: [number, number, number];
  operationalStatus: "RUNNING" | "STOPPED" | "WARNING" | "CRITICAL" | "STANDBY";
  healthScore: number;       // 0.0 - 1.0
  failureProbability: number;// 0.0 - 1.0
  rulHours: number;          // Remaining useful life
  readings: Record<string, { value: number | string; unit: string; label: string }>;
}
```

---

## 🎨 Multi-Layer Visualization Engine

1. **Power Grid Flow Layer**:
   - Animated spline paths with glowing pulses traveling from generators (`GEN-*`) through microgrid switchgear (`SWG-*`) to battery storage (`BAT-*`) and building consumption loads.
2. **Water Loop Layer**:
   - Cyan fluid flow lines tracing water intake from Lake Priyadarshini / Prydz Bay through high-pressure pump skids, filtration/RO plants, and distribution buffer tanks.
3. **Thermal Heatmap Layer**:
   - False-color emissive overlays showing temperature gradients (Sub-zero -25°C ambient blue vs +22°C interior green/yellow vs +80°C to +340°C generator exhaust red).
4. **Communications RF Layer**:
   - Conical satellite uplink beams from tracking radomes to polar orbit satellites and microwave telemetry links to the Automatic Weather Station (AWS).
5. **Meteorological Vector Layer**:
   - Real-time particle streamlines dynamically driven by simulated wind velocity and azimuth vectors.

---

## 🎥 Cinematic Camera Modes

- `ORBIT`: 360-degree free orbital camera with polar snow collision constraints (`maxPolarAngle = 1.52 rad`).
- `TOP_DOWN`: Master plan architectural layout inspection from zenith ($y = 52\text{m}$).
- `ISOMETRIC`: Axonometric engineering projection ($[30, 24, 30]$).
- `GROUND`: First-person polar explorer perspective ($y = 2.2\text{m}$).
- `FACILITY_FOCUS`: Smooth interpolation to any selected asset node.
- `AUTO_TOUR`: Smooth continuous station flyover mode.

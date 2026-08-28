# 🔬 Digital Twin In-Memory Specification & ML Prognostics

## 🧠 Digital Twin In-Memory Model
- State engine is implemented as a singleton (`DigitalTwinEngine`) in `backend/app/digital_twin/engine.py`.
- **Staleness Threshold**: If an asset node receives no telemetry for $> 5\text{ minutes}$, its connectivity state transitions to `STALE`, and its health score is clamped to $0.50$.

---

## 📐 Health & Prognostic Formulations

### 1. Multivariate Isolation Forest Anomaly Score
Trained across 6 sensor dimensions:
$$X = [\text{Temp}_{\text{gen}}, \text{RPM}_{\text{gen}}, \text{Vibration}_{\text{gen}}, \text{SOC}_{\text{batt}}, \text{Temp}_{\text{batt}}, \text{Flow}_{\text{hvac}}]$$

### 2. Multi-Factor Asset Health Score
$$\text{Health} = \max\left(0.10, \min\left(1.0, \text{Base} - (0.35 \cdot \text{Anomaly} + \Delta\text{Temp} + \Delta\text{Vib} + \Delta\text{SOC})\right)\right)$$

### 3. Estimated Remaining Useful Life (RUL)
$$\text{RUL} = \begin{cases} 
8500 \cdot (\text{Health} / 0.95) & \text{if } \text{Health} \ge 0.90 \\
2400 \cdot (\text{Health} / 0.85) & \text{if } 0.75 \le \text{Health} < 0.90 \\
320 \cdot (\text{Health} / 0.50) & \text{if } \text{Health} < 0.75 
\end{cases}$$

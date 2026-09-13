import { useEffect, useMemo, useState } from "react";

const REAL_VEHICLES = ["CUP1", "CUP2", "CUP3", "CUP4", "CUP5", "ID1", "ID2"];

export default function AIInsightsPanel() {
  const [vehicles, setVehicles] = useState([]);
  const [vehicleId, setVehicleId] = useState("CUP1");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const vehicle = useMemo(
    () => vehicles.find((v) => v.vehicle_id === vehicleId) || null,
    [vehicles, vehicleId]
  );

  async function loadVehicles() {
    const response = await fetch("/api/vehicles", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Vehicle API HTTP ${response.status}`);
    }

    const data = await response.json();
    const real = Array.isArray(data)
      ? data.filter((v) => REAL_VEHICLES.includes(v.vehicle_id))
      : [];

    setVehicles(real);

    if (real.length && !real.some((v) => v.vehicle_id === vehicleId)) {
      setVehicleId(real[0].vehicle_id);
    }
  }

  async function runInference(currentVehicle) {
    if (!currentVehicle) {
      setError("No real vehicle telemetry is available.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const payload = {
        battery_soc: Number(currentVehicle.battery),
        battery_voltage: 400.0,
        speed: Number(currentVehicle.speed),
        battery_temp:
          currentVehicle.temperature != null
            ? Number(currentVehicle.temperature)
            : 30.0,
      };

      const response = await fetch("/api/ai/real-world/risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          body.detail || `Real-world AI HTTP ${response.status}`
        );
      }

      setResult({
        ...body,
        vehicle_id: currentVehicle.vehicle_id,
        source_timestamp: currentVehicle.timestamp,
      });
    } catch (e) {
      setResult(null);
      setError(e.message || "Real-world AI inference failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let alive = true;

    const refresh = async () => {
      try {
        await loadVehicles();
      } catch (e) {
        if (alive) setError(e.message || "Vehicle API unavailable.");
      }
    };

    refresh();
    const timer = setInterval(refresh, 5000);

    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!vehicle) return;

    runInference(vehicle);
    const timer = setInterval(() => runInference(vehicle), 10000);

    return () => clearInterval(timer);
  }, [vehicle?.vehicle_id, vehicle?.timestamp, vehicle?.battery, vehicle?.speed]);

  return (
    <section
      style={{
        margin: "24px 0",
        padding: "24px",
        borderRadius: "14px",
        background: "linear-gradient(135deg,#101b2d,#16243b)",
        color: "#fff",
        border: "1px solid rgba(255,255,255,.12)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 20, alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: 1.5, opacity: .7 }}>
            AI INTELLIGENCE
          </div>
          <h2 style={{ margin: "6px 0" }}>Real-Time EV Anomaly Intelligence</h2>
          <div style={{ opacity: .75 }}>
            Production FastAPI → IsolationForest → React integration
          </div>
        </div>

        <select
          value={vehicleId}
          onChange={(e) => setVehicleId(e.target.value)}
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            fontWeight: 700,
            background: "#fff",
            color: "#111",
          }}
        >
          {REAL_VEHICLES.map((id) => (
            <option key={id} value={id}>{id}</option>
          ))}
        </select>
      </div>

      {error && (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            borderRadius: 8,
            background: "#7a2f12",
            border: "1px solid #ff9a5c",
          }}
        >
          AI service error: {error}
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))",
          gap: 12,
          marginTop: 18,
        }}
      >
        <div><small>AI STATUS</small><h3>{loading ? "RUNNING" : result ? "ONLINE" : "OFFLINE"}</h3></div>
        <div><small>ALGORITHM</small><h3>{result?.algorithm || "—"}</h3></div>
        <div><small>MODEL VERSION</small><h3>{result?.model_version || "—"}</h3></div>
        <div><small>VEHICLE</small><h3>{result?.vehicle_id || vehicleId}</h3></div>
        <div><small>ANOMALY SCORE</small><h3>{result?.anomaly_score ?? "—"}</h3></div>
      </div>

      <div
        style={{
          marginTop: 18,
          padding: 16,
          borderRadius: 10,
          background: "rgba(255,255,255,.07)",
        }}
      >
        <div style={{ fontWeight: 800 }}>AI DECISION</div>
        <div style={{ fontSize: 28, fontWeight: 900, marginTop: 6 }}>
          {result
            ? result.is_anomaly
              ? "ANOMALY DETECTED"
              : "NORMAL"
            : "UNKNOWN"}
        </div>

        {result && (
          <div style={{ marginTop: 12, lineHeight: 1.8, opacity: .9 }}>
            <div>Model ID: {result.model_id || "—"}</div>
            <div>Source: {result.model_source || "TUMFTM real-world dataset"}</div>
            <div>Artifact: {result.artifact || "Persisted production model"}</div>
            <div>Telemetry timestamp: {result.source_timestamp || "—"}</div>
          </div>
        )}
      </div>
    </section>
  );
}

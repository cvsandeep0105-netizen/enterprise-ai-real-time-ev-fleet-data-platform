import duckdb

src="/features/real_world_ev_features.parquet"
out="/features/real_world_ai_dataset.parquet"

con=duckdb.connect()

con.execute(f"""
COPY (
    SELECT
        vehicle_id,
        window_start,
        battery_soc,
        battery_voltage,
        speed,
        (battery_temp_min + battery_temp_max) / 2.0 AS battery_temp,
        battery_temp_min,
        battery_temp_max,
        battery_temp_max - battery_temp_min AS battery_temp_delta,
        ambient_temp,
        motor_stator_temp,
        motor_rotor_temp,
        inverter_coolant_temp,
        battery_inlet_temp,
        battery_outlet_temp,
        hv_aux_power
    FROM read_parquet('{src}')
    WHERE battery_soc IS NOT NULL
      AND battery_voltage IS NOT NULL
      AND speed IS NOT NULL
      AND battery_temp_min IS NOT NULL
      AND battery_temp_max IS NOT NULL
    ORDER BY vehicle_id, window_start
)
TO '{out}'
(FORMAT PARQUET, COMPRESSION ZSTD)
""")

r=con.execute(f"""
SELECT COUNT(*), COUNT(DISTINCT vehicle_id),
       MIN(window_start), MAX(window_start)
FROM read_parquet('{out}')
""").fetchone()

print("AI_ROWS =",r[0])
print("AI_VEHICLES =",r[1])
print("AI_MIN_WINDOW =",r[2])
print("AI_MAX_WINDOW =",r[3])
print("REAL_WORLD_AI_DATASET = COMPLETE")

con.close()

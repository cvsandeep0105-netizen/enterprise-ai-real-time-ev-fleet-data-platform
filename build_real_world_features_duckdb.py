import duckdb
import os

INPUT="/canonical/*.parquet"
OUTPUT="/features/real_world_ev_features.parquet"

os.makedirs("/features", exist_ok=True)

con=duckdb.connect()

query=f"""
COPY (
    SELECT
        vehicle_id,
        date_trunc('minute', timestamp) AS window_start,

        avg(value) FILTER (WHERE signal_name='vehicle_speed') AS speed,
        avg(value) FILTER (WHERE signal_name='ambient_air_temp') AS ambient_temp,
        avg(value) FILTER (WHERE signal_name='hv_soc') AS battery_soc,
        avg(value) FILTER (WHERE signal_name='hv_battery_voltage') AS battery_voltage,

        avg(value) FILTER (WHERE signal_name='hv_temp_min') AS battery_temp_min,
        avg(value) FILTER (WHERE signal_name='hv_temp_max') AS battery_temp_max,

        avg(value) FILTER (WHERE signal_name='temp_rear_motor_stator') AS motor_stator_temp,
        avg(value) FILTER (WHERE signal_name='rear_motor_rotor_temp') AS motor_rotor_temp,
        avg(value) FILTER (WHERE signal_name='coolant_temp_inverter_inlet') AS inverter_coolant_temp,

        avg(value) FILTER (WHERE signal_name='hv_battery_temp_inlet') AS battery_inlet_temp,
        avg(value) FILTER (WHERE signal_name='hv_battery_temp_outlet') AS battery_outlet_temp,

        avg(value) FILTER (WHERE signal_name='hv_aux_power') AS hv_aux_power,

        count(*) FILTER (WHERE signal_name='vehicle_speed') AS speed_samples,
        count(*) FILTER (WHERE signal_name='hv_soc') AS soc_samples,
        count(*) FILTER (WHERE signal_name='hv_battery_voltage') AS voltage_samples,
        count(*) FILTER (WHERE signal_name='hv_temp_min') AS temp_min_samples,
        count(*) FILTER (WHERE signal_name='hv_temp_max') AS temp_max_samples

    FROM read_parquet('{INPUT}', union_by_name=true)
    WHERE timestamp < TIMESTAMP '2024-01-01'
    GROUP BY vehicle_id, date_trunc('minute', timestamp)
    ORDER BY vehicle_id, window_start
)
TO '{OUTPUT}'
(FORMAT PARQUET, COMPRESSION ZSTD);
"""

con.execute(query)

count=con.execute(
    f"SELECT COUNT(*) FROM read_parquet('{OUTPUT}')"
).fetchone()[0]

print("FEATURE_ROWS =",count)
print("FEATURE_OUTPUT =",OUTPUT)
print("FEATURE_ENGINEERING = COMPLETE")

con.close()

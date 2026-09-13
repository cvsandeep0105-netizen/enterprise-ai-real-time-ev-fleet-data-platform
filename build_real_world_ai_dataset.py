import duckdb
import os

os.makedirs("/features",exist_ok=True)

con=duckdb.connect()
con.execute("SET threads=4")
con.execute("SET memory_limit='4GB'")

src="/canonical/*.parquet"
out="/features/real_world_ai_dataset.parquet"

query=f"""
COPY (
WITH
soc AS (
    SELECT vehicle_id,timestamp,battery_soc
    FROM (
        SELECT vehicle_id,timestamp,value AS battery_soc,
               ROW_NUMBER() OVER(PARTITION BY vehicle_id,timestamp ORDER BY timestamp) rn
        FROM read_parquet('{src}',union_by_name=true)
        WHERE signal_name='hv_soc'
    )
    WHERE rn=1
),
speed AS (
    SELECT vehicle_id,timestamp,value AS speed
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='vehicle_speed'
),
voltage AS (
    SELECT vehicle_id,timestamp,value AS battery_voltage
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='hv_battery_voltage'
),
ambient AS (
    SELECT vehicle_id,timestamp,value AS ambient_temp
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='ambient_air_temp'
),
temp_min AS (
    SELECT vehicle_id,timestamp,value AS battery_temp_min
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='hv_temp_min'
),
temp_max AS (
    SELECT vehicle_id,timestamp,value AS battery_temp_max
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='hv_temp_max'
),
motor_stator AS (
    SELECT vehicle_id,timestamp,value AS motor_stator_temp
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='temp_rear_motor_stator'
),
motor_rotor AS (
    SELECT vehicle_id,timestamp,value AS motor_rotor_temp
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='rear_motor_rotor_temp'
),
coolant AS (
    SELECT vehicle_id,timestamp,value AS inverter_coolant_temp
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='coolant_temp_inverter_inlet'
),
inlet AS (
    SELECT vehicle_id,timestamp,value AS battery_inlet_temp
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='hv_battery_temp_inlet'
),
outlet AS (
    SELECT vehicle_id,timestamp,value AS battery_outlet_temp
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='hv_battery_temp_outlet'
),
aux AS (
    SELECT vehicle_id,timestamp,value AS hv_aux_power
    FROM read_parquet('{src}',union_by_name=true)
    WHERE signal_name='hv_aux_power'
),
aligned AS (
    SELECT
        s.vehicle_id,
        s.timestamp,

        s.battery_soc,

        sp.speed,
        v.battery_voltage,
        a.ambient_temp,

        tm.battery_temp_min,
        tx.battery_temp_max,

        ms.motor_stator_temp,
        mr.motor_rotor_temp,
        c.inverter_coolant_temp,

        bi.battery_inlet_temp,
        bo.battery_outlet_temp,
        ax.hv_aux_power

    FROM soc s

    ASOF LEFT JOIN speed sp
      ON s.vehicle_id=sp.vehicle_id
     AND s.timestamp>=sp.timestamp

    ASOF LEFT JOIN voltage v
      ON s.vehicle_id=v.vehicle_id
     AND s.timestamp>=v.timestamp

    ASOF LEFT JOIN ambient a
      ON s.vehicle_id=a.vehicle_id
     AND s.timestamp>=a.timestamp

    ASOF LEFT JOIN temp_min tm
      ON s.vehicle_id=tm.vehicle_id
     AND s.timestamp>=tm.timestamp

    ASOF LEFT JOIN temp_max tx
      ON s.vehicle_id=tx.vehicle_id
     AND s.timestamp>=tx.timestamp

    ASOF LEFT JOIN motor_stator ms
      ON s.vehicle_id=ms.vehicle_id
     AND s.timestamp>=ms.timestamp

    ASOF LEFT JOIN motor_rotor mr
      ON s.vehicle_id=mr.vehicle_id
     AND s.timestamp>=mr.timestamp

    ASOF LEFT JOIN coolant c
      ON s.vehicle_id=c.vehicle_id
     AND s.timestamp>=c.timestamp

    ASOF LEFT JOIN inlet bi
      ON s.vehicle_id=bi.vehicle_id
     AND s.timestamp>=bi.timestamp

    ASOF LEFT JOIN outlet bo
      ON s.vehicle_id=bo.vehicle_id
     AND s.timestamp>=bo.timestamp

    ASOF LEFT JOIN aux ax
      ON s.vehicle_id=ax.vehicle_id
     AND s.timestamp>=ax.timestamp
)
SELECT
    vehicle_id,
    timestamp,

    battery_soc,
    speed,
    battery_voltage,
    ambient_temp,

    battery_temp_min,
    battery_temp_max,
    battery_temp_max-battery_temp_min AS battery_temp_delta,

    motor_stator_temp,
    motor_rotor_temp,
    inverter_coolant_temp,

    battery_inlet_temp,
    battery_outlet_temp,
    hv_aux_power,

    CASE
        WHEN battery_soc IS NOT NULL
         AND battery_voltage IS NOT NULL
         AND speed IS NOT NULL
        THEN TRUE ELSE FALSE
    END AS core_features_available

FROM aligned
ORDER BY vehicle_id,timestamp
)
TO '{out}'
(FORMAT PARQUET,COMPRESSION ZSTD);
"""

con.execute(query)

result=con.execute(
    f"""
    SELECT
      COUNT(*) AS rows,
      COUNT(DISTINCT vehicle_id) AS vehicles,
      COUNT(*) FILTER(WHERE core_features_available) AS usable_core_rows
    FROM read_parquet('{out}')
    """
).fetchone()

print("AI_DATASET_ROWS =",result[0])
print("AI_DATASET_VEHICLES =",result[1])
print("AI_DATASET_CORE_ROWS =",result[2])
print("AI_DATASET_OUTPUT =",out)
print("REAL_WORLD_AI_DATASET = COMPLETE")

con.close()

import pyarrow.parquet as pq
import pyarrow as pa
import glob
import os

src="/canonical"
out="/spark_ready"
os.makedirs(out, exist_ok=True)

for f in sorted(glob.glob(os.path.join(src, "*.parquet"))):
    name=os.path.basename(f)
    target=os.path.join(out, name)

    table=pq.read_table(f)
    idx=table.schema.get_field_index("timestamp")
    timestamp=table["timestamp"].cast(pa.timestamp("us"))

    table=table.set_column(idx, "timestamp", timestamp)
    pq.write_table(table, target, compression="zstd")

    print(name, "ROWS =", table.num_rows)

print("SPARK_READY_CANONICAL_COMPLETE")

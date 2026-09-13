import concurrent.futures
import json
import os
import statistics
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
EVIDENCE = ROOT / "performance" / "area28_final_acceptance.json"
EVIDENCE.parent.mkdir(parents=True, exist_ok=True)

result = {
    "area": 28,
    "title": "Performance & Scalability",
    "started_at": datetime.now().isoformat(),
    "checks": {},
}

def check(name, fn):
    try:
        value = fn()
        result["checks"][name] = {"status": "PASS", "details": value}
        print(f"[PASS] {name}")
        return True
    except Exception as exc:
        result["checks"][name] = {"status": "FAIL", "error": str(exc)}
        print(f"[FAIL] {name}: {exc}")
        return False

def api_concurrency():
    target = "http://127.0.0.1:8000/"
    total = 60
    workers = 10

    def request():
        start = time.perf_counter()
        with urllib.request.urlopen(target, timeout=15) as r:
            body = r.read()
            status = r.status
        return status, len(body), (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        samples = list(pool.map(lambda _: request(), range(total)))
    wall_ms = (time.perf_counter() - start) * 1000

    if any(status != 200 for status, _, _ in samples):
        raise RuntimeError("One or more concurrent API requests returned non-200")

    latencies = sorted(x[2] for x in samples)
    p95 = latencies[min(len(latencies)-1, int(len(latencies)*0.95))]

    return {
        "requests": total,
        "concurrency": workers,
        "successful": len(samples),
        "min_ms": round(min(latencies), 3),
        "mean_ms": round(statistics.mean(latencies), 3),
        "p50_ms": round(statistics.median(latencies), 3),
        "p95_ms": round(p95, 3),
        "max_ms": round(max(latencies), 3),
        "wall_time_ms": round(wall_ms, 3),
    }

def postgres_validation():
    import psycopg2

    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("ANALYZE ev_data")

    cur.execute("SELECT count(*) FROM ev_data")
    rows = cur.fetchone()[0]
    if rows < 20000:
        raise RuntimeError(f"Expected at least 20,000 ev_data rows, found {rows}")

    sql = """
    SELECT event_id, vehicle_id, timestamp, battery, speed
    FROM ev_data
    WHERE vehicle_id = 'EV-001'
    ORDER BY timestamp DESC
    LIMIT 50
    """

    timings = []
    for _ in range(20):
        start = time.perf_counter()
        cur.execute(sql)
        data = cur.fetchall()
        timings.append((time.perf_counter() - start) * 1000)
        if len(data) != 50:
            raise RuntimeError(f"Expected 50 rows, received {len(data)}")

    cur.execute("""
    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
    SELECT event_id, vehicle_id, timestamp, battery, speed
    FROM ev_data
    WHERE vehicle_id = 'EV-001'
    ORDER BY timestamp DESC
    LIMIT 50
    """)
    plan = cur.fetchone()[0][0]["Plan"]

    node = plan["Plans"][0]
    index_name = node.get("Index Name", "")
    actual_rows = plan.get("Actual Rows", 0)
    execution_ms = plan.get("Actual Total Time", 0)

    if node.get("Node Type") != "Index Scan":
        raise RuntimeError(f"Expected Index Scan, got {node.get('Node Type')}")

    if "vehicle_timestamp" not in index_name:
        raise RuntimeError(f"Expected vehicle/timestamp composite index, got {index_name}")

    if node.get("Scan Direction") != "Backward":
        raise RuntimeError("Expected backward index scan for timestamp DESC")

    if actual_rows != 50:
        raise RuntimeError(f"Expected 50 actual rows, got {actual_rows}")

    return {
        "row_count": rows,
        "samples": 20,
        "min_ms": round(min(timings), 3),
        "mean_ms": round(statistics.mean(timings), 3),
        "p50_ms": round(statistics.median(timings), 3),
        "p95_ms": round(sorted(timings)[min(19, int(20*0.95))], 3),
        "index_name": index_name,
        "scan_direction": node.get("Scan Direction"),
        "actual_rows": actual_rows,
        "execution_time_ms": execution_ms,
        "shared_read_blocks": node.get("Shared Read Blocks", 0),
        "temp_read_blocks": node.get("Temp Read Blocks", 0),
        "temp_written_blocks": node.get("Temp Written Blocks", 0),
    }

def backend_tests():
    commands = [
        ["python", "-m", "pytest", "tests", "-q"],
    ]
    for cmd in commands:
        completed = subprocess.run(
            cmd,
            cwd=ROOT / "backend",
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Backend test suite failed:\n" + completed.stdout[-5000:] +
                "\n" + completed.stderr[-5000:]
            )
    return {"command": "python -m pytest tests -q", "status": "all passed"}

def regression_tests():
    completed = subprocess.run(
        ["python", "-m", "pytest",
         "tests/test_area24_cicd.py",
         "tests/test_area27_cicd.py",
         "tests/test_area28_performance.py",
         "-q"],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Regression/performance tests failed:\n" +
            completed.stdout[-5000:] + "\n" +
            completed.stderr[-5000:]
        )
    return {
        "tests": [
            "test_area24_cicd.py",
            "test_area27_cicd.py",
            "test_area28_performance.py",
        ],
        "status": "all passed",
    }

def artifact_validation():
    required = [
        ROOT / "performance" / "api_benchmark.py",
        ROOT / "performance" / "postgres_baseline.py",
        ROOT / "performance" / "latest_api_benchmark.json",
        ROOT / "performance" / "postgres_baseline.json",
        ROOT / "spark" / "cache_analysis.py",
        ROOT / "spark" / "partition_analysis.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise RuntimeError("Missing performance artifacts: " + ", ".join(missing))
    return {"required_artifacts": len(required), "missing": 0}

def kubernetes_validation():
    completed = subprocess.run(
        ["kubectl", "get", "deployments", "-n", "ev-fleet",
         "-o", "json"],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr)

    data = json.loads(completed.stdout)
    deployments = []
    for item in data["items"]:
        name = item["metadata"]["name"]
        desired = item["spec"].get("replicas", 0)
        available = item["status"].get("availableReplicas", 0)
        if desired != available:
            raise RuntimeError(
                f"Deployment {name}: desired={desired}, available={available}"
            )
        deployments.append({
            "name": name,
            "desired": desired,
            "available": available,
        })

    return {"deployments": deployments}

checks = [
    ("API concurrency performance", api_concurrency),
    ("PostgreSQL 20K scalability and query plan", postgres_validation),
    ("Complete backend test suite", backend_tests),
    ("Area 24/27 regression and Area 28 tests", regression_tests),
    ("Performance/Spark artifact validation", artifact_validation),
    ("Kubernetes deployment validation", kubernetes_validation),
]

for name, fn in checks:
    if not check(name, fn):
        result["status"] = "FAIL"
        result["completed_at"] = datetime.now().isoformat()
        EVIDENCE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(1)

result["status"] = "PASS"
result["completed_at"] = datetime.now().isoformat()
EVIDENCE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

print("\n" + "=" * 70)
print("AREA 28 FINAL ACCEPTANCE")
print("=" * 70)
print("STATUS: PASS")
print("All Area 28 performance, scalability, regression, hardening,")
print("artifact, and Kubernetes validation checks passed.")
print(f"Evidence: {EVIDENCE}")
print("=" * 70)
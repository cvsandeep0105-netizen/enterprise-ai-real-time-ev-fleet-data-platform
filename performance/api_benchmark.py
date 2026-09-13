import json
import statistics
import time
import urllib.request
from pathlib import Path

TARGET = "http://127.0.0.1:8000/"
REQUESTS = 20
TIMEOUT = 10

def request_once():
    start = time.perf_counter()
    with urllib.request.urlopen(TARGET, timeout=TIMEOUT) as response:
        body = response.read()
        status = response.status
    elapsed_ms = (time.perf_counter() - start) * 1000
    return status, len(body), elapsed_ms

def main():
    samples = []
    for _ in range(REQUESTS):
        status, size, elapsed = request_once()
        if status != 200:
            raise RuntimeError(f"Unexpected HTTP status: {status}")
        samples.append(elapsed)

    samples_sorted = sorted(samples)
    p50 = statistics.median(samples_sorted)
    p95_index = min(len(samples_sorted) - 1, int(len(samples_sorted) * 0.95))
    p95 = samples_sorted[p95_index]

    result = {
        "target": TARGET,
        "requests": REQUESTS,
        "successful_requests": REQUESTS,
        "min_ms": round(min(samples_sorted), 3),
        "mean_ms": round(statistics.mean(samples_sorted), 3),
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "max_ms": round(max(samples_sorted), 3),
    }

    print(json.dumps(result, indent=2))

    Path("performance").mkdir(exist_ok=True)
    Path("performance/latest_api_benchmark.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
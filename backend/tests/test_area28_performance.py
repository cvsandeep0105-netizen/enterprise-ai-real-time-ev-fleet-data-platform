from pathlib import Path
import ast

BENCHMARK = Path("performance/api_benchmark.py")

def test_performance_benchmark_exists():
    assert BENCHMARK.exists()

def test_performance_benchmark_is_valid_python():
    source = BENCHMARK.read_text(encoding="utf-8")
    assert not source.startswith("\ufeff")
    ast.parse(source)

def test_benchmark_has_repeatable_measurement_contract():
    source = BENCHMARK.read_text(encoding="utf-8")
    for required in [
        "REQUESTS",
        "TIMEOUT",
        "perf_counter",
        "p50_ms",
        "p95_ms",
        "successful_requests",
        "latest_api_benchmark.json",
    ]:
        assert required in source
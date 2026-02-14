#!/usr/bin/env python3
"""Run API runtime load against an HTTP endpoint."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _percentile(values_sorted: list[float], p: float) -> float:
    if not values_sorted:
        return 0.0
    if len(values_sorted) == 1:
        return values_sorted[0]
    pos = (len(values_sorted) - 1) * p
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return values_sorted[lo]
    return values_sorted[lo] + (values_sorted[hi] - values_sorted[lo]) * (pos - lo)


def _request_once(
    *, url: str, method: str, headers: dict[str, str], payload: bytes | None, timeout_seconds: float
) -> dict[str, Any]:
    started = time.perf_counter()
    request = urllib.request.Request(url=url, data=payload, method=method, headers=headers)
    status_code = 0
    ok = False
    error: str | None = None
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(getattr(response, "status", 200))
            _ = response.read()
            ok = 200 <= status_code < 400
            if not ok:
                error = f"http_status_{status_code}"
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        _ = exc.read()
        error = f"http_status_{status_code}"
    except Exception as exc:  # pragma: no cover
        error = str(exc)
    return {
        "ok": ok,
        "status_code": status_code,
        "latency_ms": (time.perf_counter() - started) * 1000,
        "error": error,
    }


def _run_load(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    payload: bytes | None,
    timeout_seconds: float,
    concurrency: int,
    duration_seconds: float,
    total_requests: int | None,
) -> tuple[list[dict[str, Any]], float]:
    samples: list[dict[str, Any]] = []
    samples_lock = threading.Lock()
    count = 0
    count_lock = threading.Lock()
    started = time.perf_counter()
    stop_at = started + duration_seconds

    def next_slot() -> bool:
        nonlocal count
        with count_lock:
            if total_requests is not None:
                if count >= total_requests:
                    return False
            elif time.perf_counter() >= stop_at:
                return False
            count += 1
            return True

    def worker() -> None:
        local: list[dict[str, Any]] = []
        while next_slot():
            local.append(
                _request_once(
                    url=url,
                    method=method,
                    headers=headers,
                    payload=payload,
                    timeout_seconds=timeout_seconds,
                )
            )
        if local:
            with samples_lock:
                samples.extend(local)

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        futures = [executor.submit(worker) for _ in range(max(1, concurrency))]
        for future in futures:
            future.result()
    return samples, (time.perf_counter() - started)


def _build_metrics(samples: list[dict[str, Any]], elapsed_seconds: float) -> dict[str, float | int]:
    total_requests = len(samples)
    success_count = sum(1 for s in samples if bool(s["ok"]))
    failure_count = total_requests - success_count
    latencies = sorted(float(s["latency_ms"]) for s in samples)
    metrics: dict[str, float | int] = {
        "elapsed_seconds": elapsed_seconds,
        "total_requests": total_requests,
        "success_count": success_count,
        "failure_count": failure_count,
        "error_rate_pct": (failure_count / total_requests * 100.0) if total_requests else 100.0,
        "requests_per_second": (total_requests / elapsed_seconds) if elapsed_seconds > 0 else 0.0,
        "latency_min_ms": 0.0,
        "latency_mean_ms": 0.0,
        "latency_p50_ms": 0.0,
        "latency_p90_ms": 0.0,
        "latency_p95_ms": 0.0,
        "latency_p99_ms": 0.0,
        "latency_max_ms": 0.0,
    }
    if latencies:
        metrics["latency_min_ms"] = latencies[0]
        metrics["latency_mean_ms"] = statistics.mean(latencies)
        metrics["latency_p50_ms"] = _percentile(latencies, 0.50)
        metrics["latency_p90_ms"] = _percentile(latencies, 0.90)
        metrics["latency_p95_ms"] = _percentile(latencies, 0.95)
        metrics["latency_p99_ms"] = _percentile(latencies, 0.99)
        metrics["latency_max_ms"] = latencies[-1]
    return metrics


def _evaluate_thresholds(
    *,
    metrics: dict[str, float | int],
    max_error_rate_pct: float,
    max_p95_latency_ms: float | None,
    min_rps: float | None,
) -> list[str]:
    failures: list[str] = []
    total_requests = int(metrics.get("total_requests", 0))
    error_rate_pct = float(metrics.get("error_rate_pct", 0.0))
    p95_ms = float(metrics.get("latency_p95_ms", 0.0))
    rps = float(metrics.get("requests_per_second", 0.0))
    if total_requests <= 0:
        failures.append("no_requests_executed")
    if error_rate_pct > max_error_rate_pct:
        failures.append(
            f"error_rate_pct={error_rate_pct:.2f} exceeds max_error_rate_pct={max_error_rate_pct:.2f}"
        )
    if max_p95_latency_ms is not None and p95_ms > max_p95_latency_ms:
        failures.append(
            f"latency_p95_ms={p95_ms:.2f} exceeds max_p95_latency_ms={max_p95_latency_ms:.2f}"
        )
    if min_rps is not None and rps < min_rps:
        failures.append(f"requests_per_second={rps:.2f} below min_rps={min_rps:.2f}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run API runtime load against an HTTP endpoint")
    parser.add_argument("--name", default="api_runtime_load", help="Logical name for this load run")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument(
        "--endpoint", default="/api/v1/health", help="Endpoint path or absolute URL"
    )
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        help="HTTP method",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="HTTP header in 'Name: Value' form (repeatable)",
    )
    parser.add_argument("--payload", default=None, help="Raw request payload")
    parser.add_argument(
        "--payload-file", type=Path, default=None, help="File containing payload bytes"
    )
    parser.add_argument("--concurrency", type=int, default=8, help="Concurrent workers")
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=15.0,
        help="Load duration in seconds (ignored when --total-requests is set)",
    )
    parser.add_argument(
        "--total-requests",
        type=int,
        default=None,
        help="Fixed request count (overrides --duration-seconds)",
    )
    parser.add_argument("--timeout-seconds", type=float, default=5.0, help="Per-request timeout")
    parser.add_argument("--warmup-requests", type=int, default=3, help="Warmup requests")
    parser.add_argument(
        "--max-error-rate-pct",
        type=float,
        default=0.0,
        help="Fail when error rate exceeds this percentage",
    )
    parser.add_argument(
        "--max-p95-latency-ms",
        type=float,
        default=None,
        help="Optional p95 latency threshold in milliseconds",
    )
    parser.add_argument(
        "--min-rps",
        type=float,
        default=None,
        help="Optional minimum sustained requests/sec threshold",
    )
    parser.add_argument(
        "--output-json", type=Path, default=None, help="Write full report to JSON path"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        headers: dict[str, str] = {"Accept": "application/json"}
        for raw in list(args.header):
            if ":" not in raw:
                raise ValueError(f"invalid --header value: {raw!r} (expected 'Name: Value')")
            name, value = raw.split(":", 1)
            key = name.strip()
            if not key:
                raise ValueError(f"invalid --header value: {raw!r} (empty header name)")
            headers[key] = value.strip()
        if args.payload is not None and args.payload_file is not None:
            raise ValueError("use either --payload or --payload-file, not both")
        payload = args.payload_file.read_bytes() if args.payload_file else None
        if payload is None and args.payload is not None:
            payload = str(args.payload).encode("utf-8")
        endpoint = str(args.endpoint)
        url = (
            endpoint
            if endpoint.startswith(("http://", "https://"))
            else f"{str(args.base_url).rstrip('/')}/{endpoint.lstrip('/')}"
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    for _ in range(max(0, int(args.warmup_requests))):
        _request_once(
            url=url,
            method=str(args.method),
            headers=headers,
            payload=payload,
            timeout_seconds=max(0.1, float(args.timeout_seconds)),
        )

    samples, elapsed_seconds = _run_load(
        url=url,
        method=str(args.method),
        headers=headers,
        payload=payload,
        timeout_seconds=max(0.1, float(args.timeout_seconds)),
        concurrency=max(1, int(args.concurrency)),
        duration_seconds=max(0.1, float(args.duration_seconds)),
        total_requests=(None if args.total_requests is None else max(1, int(args.total_requests))),
    )
    metrics = _build_metrics(samples=samples, elapsed_seconds=elapsed_seconds)
    threshold_failures = _evaluate_thresholds(
        metrics=metrics,
        max_error_rate_pct=float(args.max_error_rate_pct),
        max_p95_latency_ms=(
            None if args.max_p95_latency_ms is None else float(args.max_p95_latency_ms)
        ),
        min_rps=(None if args.min_rps is None else float(args.min_rps)),
    )

    report: dict[str, Any] = {
        "name": str(args.name),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not threshold_failures else "fail",
        "target": {
            "base_url": str(args.base_url),
            "endpoint": str(args.endpoint),
            "resolved_url": url,
            "method": str(args.method),
        },
        "config": {
            "concurrency": int(args.concurrency),
            "duration_seconds": float(args.duration_seconds),
            "total_requests": args.total_requests,
            "timeout_seconds": float(args.timeout_seconds),
            "warmup_requests": int(args.warmup_requests),
        },
        "thresholds": {
            "max_error_rate_pct": float(args.max_error_rate_pct),
            "max_p95_latency_ms": args.max_p95_latency_ms,
            "min_rps": args.min_rps,
        },
        "metrics": metrics,
        "threshold_failures": threshold_failures,
        "sample_failures": [
            {
                "status_code": int(s["status_code"]),
                "latency_ms": float(s["latency_ms"]),
                "error": str(s.get("error") or ""),
            }
            for s in samples
            if not bool(s["ok"])
        ][:5],
    }

    print("=" * 70)
    print("API RUNTIME LOAD REPORT")
    print("=" * 70)
    print(f"Name: {report['name']}")
    print(f"Target: {url}")
    print(
        f"Requests: {int(metrics['total_requests'])} total, {int(metrics['success_count'])} success, {int(metrics['failure_count'])} failure"
    )
    print(
        f"Latency (ms): p50={float(metrics['latency_p50_ms']):.2f} p95={float(metrics['latency_p95_ms']):.2f} p99={float(metrics['latency_p99_ms']):.2f}"
    )
    print(
        f"Throughput: {float(metrics['requests_per_second']):.2f} req/s | Error rate: {float(metrics['error_rate_pct']):.2f}%"
    )
    if threshold_failures:
        print("Threshold status: FAIL")
        for failure in threshold_failures:
            print(f"  - {failure}")
    else:
        print("Threshold status: PASS")

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(f"JSON report: {args.output_json}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

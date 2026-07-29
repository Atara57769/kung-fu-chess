import time
import math
import asyncio
import logging
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.parse
import json

from services.observability_service import config

logger = logging.getLogger("ObservabilityService.LoadTest")


class LoadTester:
    """Synthetic load test engine for benchmarking system throughput and latency."""

    def __init__(self):
        self.status = "idle"
        self.latest_result: Optional[Dict[str, Any]] = None
        self._current_task: Optional[asyncio.Task] = None

    async def execute_user_session(
        self,
        user_id: int,
        target_url: str,
        duration_seconds: float,
        latencies: List[float],
        counters: Dict[str, int]
    ) -> None:
        """Simulates single virtual user activity for duration_seconds."""
        end_time = time.time() + duration_seconds
        username = f"bot_user_{user_id}_{int(time.time())}"
        password = "loadtest_pass_123"
        loop = asyncio.get_running_loop()

        def _make_http_request(url: str, method: str = "GET", data: Optional[dict] = None) -> float:
            start = time.time()
            try:
                headers = {"Content-Type": "application/json", "User-Agent": "KungFuChess-LoadTester/1.0"}
                body_bytes = json.dumps(data).encode("utf-8") if data else None
                req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=3) as resp:
                    resp.read()
                elapsed = (time.time() - start) * 1000
                counters["success"] += 1
                return elapsed
            except Exception:
                counters["failed"] += 1
                return (time.time() - start) * 1000

        # Phase 1: Login / Register
        login_url = f"{target_url.rstrip('/')}/auth/login"
        lat = await loop.run_in_executor(None, _make_http_request, login_url, "POST", {"username": username, "password": password})
        latencies.append(lat)
        counters["total"] += 1

        # Loop until test duration finishes
        while time.time() < end_time:
            # Action: List Rooms
            rooms_url = f"{target_url.rstrip('/')}/rooms"
            lat = await loop.run_in_executor(None, _make_http_request, rooms_url, "GET", None)
            latencies.append(lat)
            counters["total"] += 1

            # Action: Health check
            health_url = f"{target_url.rstrip('/')}/healthz"
            lat = await loop.run_in_executor(None, _make_http_request, health_url, "GET", None)
            latencies.append(lat)
            counters["total"] += 1

            await asyncio.sleep(0.05)

    async def run_load_test(
        self,
        num_users: int = 10,
        duration_seconds: float = 5.0,
        target_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Runs synthetic load test across num_users concurrent workers."""
        if self.status == "running":
            raise RuntimeError("Load test is already in progress.")

        self.status = "running"
        target_url = target_url or config.API_GATEWAY_URL
        latencies: List[float] = []
        counters: Dict[str, int] = {"total": 0, "success": 0, "failed": 0}

        start_time = time.time()
        logger.info("Starting load test: %d virtual users for %.1f seconds targeting %s", num_users, duration_seconds, target_url)

        try:
            tasks = [
                self.execute_user_session(i, target_url, duration_seconds, latencies, counters)
                for i in range(num_users)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error("Load test error: %s", e)
        finally:
            elapsed = time.time() - start_time
            self.status = "completed"

        total_reqs = counters["total"]
        rps = round(total_reqs / elapsed, 2) if elapsed > 0 else 0.0

        if latencies:
            sorted_lat = sorted(latencies)
            n = len(sorted_lat)
            p95_idx = int(math.ceil(0.95 * n)) - 1
            min_lat = round(sorted_lat[0], 2)
            max_lat = round(sorted_lat[-1], 2)
            avg_lat = round(sum(sorted_lat) / n, 2)
            p95_lat = round(sorted_lat[max(0, p95_idx)], 2)
        else:
            min_lat = max_lat = avg_lat = p95_lat = 0.0

        self.latest_result = {
            "num_users": num_users,
            "duration_seconds": round(elapsed, 2),
            "target_url": target_url,
            "total_requests": total_reqs,
            "successful_requests": counters["success"],
            "failed_requests": counters["failed"],
            "requests_per_second": rps,
            "latency_ms": {
                "min": min_lat,
                "max": max_lat,
                "avg": avg_lat,
                "p95": p95_lat
            },
            "completed_at": time.time()
        }
        logger.info("Load test completed: RPS=%.2f, Total Reqs=%d, p95 Latency=%.2f ms", rps, total_reqs, p95_lat)
        return self.latest_result

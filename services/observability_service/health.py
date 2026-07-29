import time
import asyncio
import logging
from typing import Dict, Any
import urllib.request
import urllib.error

from services.observability_service import config

logger = logging.getLogger("ObservabilityService.Health")


class ClusterHealthChecker:
    """Asynchronous cluster health checking probe engine."""

    def __init__(self):
        self.api_url = config.API_GATEWAY_URL
        self.ws_url = config.WS_GATEWAY_URL

    async def check_http_endpoint(self, name: str, url: str) -> Dict[str, Any]:
        """Probes an HTTP healthz endpoint."""
        start = time.time()
        loop = asyncio.get_running_loop()

        def _request():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "KungFuChess-Observability/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    return resp.status == 200
            except Exception:
                return False

        try:
            is_ok = await loop.run_in_executor(None, _request)
            elapsed = (time.time() - start) * 1000
            return {
                "status": "ok" if is_ok else "unreachable",
                "latency_ms": round(elapsed, 2)
            }
        except Exception as e:
            return {"status": "unreachable", "error": str(e), "latency_ms": 0.0}

    async def check_redis(self, host: str = config.REDIS_HOST, port: int = config.REDIS_PORT) -> Dict[str, Any]:
        """Probes Redis connection."""
        start = time.time()
        try:
            import redis.asyncio as aioredis
            client = aioredis.Redis(host=host, port=port, socket_timeout=2)
            res = await client.ping()
            await client.aclose()
            elapsed = (time.time() - start) * 1000
            return {
                "status": "ok" if res else "error",
                "latency_ms": round(elapsed, 2)
            }
        except Exception as e:
            return {"status": "unreachable", "error": str(e), "latency_ms": 0.0}

    async def check_postgres(self) -> Dict[str, Any]:
        """Probes PostgreSQL database connection."""
        start = time.time()
        loop = asyncio.get_running_loop()

        def _db_ping():
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=config.POSTGRES_HOST,
                    port=config.POSTGRES_PORT,
                    user=config.POSTGRES_USER,
                    password=config.POSTGRES_PASSWORD,
                    dbname=config.POSTGRES_DB,
                    connect_timeout=2
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                res = cursor.fetchone()
                conn.close()
                return res is not None and res[0] == 1
            except Exception:
                return False

        try:
            is_ok = await loop.run_in_executor(None, _db_ping)
            elapsed = (time.time() - start) * 1000
            return {
                "status": "ok" if is_ok else "unreachable",
                "latency_ms": round(elapsed, 2)
            }
        except Exception as e:
            return {"status": "unreachable", "error": str(e), "latency_ms": 0.0}

    async def check_nats(self, nats_bus: Any = None) -> Dict[str, Any]:
        """Probes NATS connection state."""
        start = time.time()
        try:
            if nats_bus and hasattr(nats_bus, "nc") and nats_bus.nc and nats_bus.nc.is_connected:
                elapsed = (time.time() - start) * 1000
                return {"status": "ok", "latency_ms": round(elapsed, 2)}
            return {"status": "disconnected", "latency_ms": 0.0}
        except Exception as e:
            return {"status": "error", "error": str(e), "latency_ms": 0.0}

    async def run_full_system_check(self, nats_bus: Any = None) -> Dict[str, Any]:
        """Runs all probe checks concurrently and builds composite cluster status."""
        results = await asyncio.gather(
            self.check_postgres(),
            self.check_redis(),
            self.check_nats(nats_bus),
            self.check_http_endpoint("api_gateway", f"{self.api_url}/healthz"),
            self.check_http_endpoint("websocket_gateway", f"{self.ws_url}/healthz"),
            return_exceptions=True
        )

        components = {
            "postgres": results[0] if isinstance(results[0], dict) else {"status": "unreachable"},
            "redis": results[1] if isinstance(results[1], dict) else {"status": "unreachable"},
            "nats": results[2] if isinstance(results[2], dict) else {"status": "unreachable"},
            "api_gateway": results[3] if isinstance(results[3], dict) else {"status": "unreachable"},
            "websocket_gateway": results[4] if isinstance(results[4], dict) else {"status": "unreachable"},
        }

        ok_count = sum(1 for c in components.values() if c.get("status") == "ok")
        total_count = len(components)

        if ok_count == total_count:
            overall_status = "HEALTHY"
        elif ok_count > 0:
            overall_status = "DEGRADED"
        else:
            overall_status = "UNHEALTHY"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "healthy_components": ok_count,
            "total_components": total_count,
            "components": components
        }

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from services.observability_service.logs import LogCollector
from services.observability_service.metrics import MetricsCollector, MetricType
from services.observability_service.health import ClusterHealthChecker
from services.observability_service.load_test import LoadTester
from services.observability_service.app import (
    health_check, record_metric, get_prometheus_metrics,
    get_json_metrics, ingest_log, query_logs,
    get_load_test_status, get_load_test_results,
    RecordMetricRequest, LogIngestRequest
)


def test_log_collector_ingest_and_query():
    collector = LogCollector(max_entries=100)
    collector.ingest_log(service="game_server", level="INFO", message="Server initialized")
    collector.ingest_log(service="api_gateway", level="ERROR", message="Auth failure for user alice")
    collector.ingest_log(service="game_server", level="WARN", message="High latency detected on move")

    # Query all
    all_logs = collector.query_logs(limit=10)
    assert len(all_logs) == 3

    # Filter by service
    gs_logs = collector.query_logs(service="game_server")
    assert len(gs_logs) == 2

    # Filter by level
    err_logs = collector.query_logs(level="ERROR")
    assert len(err_logs) == 1
    assert err_logs[0]["service"] == "api_gateway"

    # Search keyword
    search_logs = collector.query_logs(search="latency")
    assert len(search_logs) == 1
    assert search_logs[0]["level"] == "WARN"


def test_log_collector_nats_callback():
    async def _test():
        collector = LogCollector()
        event_data = {
            "service": "matchmaking_service",
            "level": "INFO",
            "message": "Match created for players A and B",
            "metadata": {"room_id": "room_123"}
        }
        await collector.handle_nats_log_event(event_data)
        logs = collector.query_logs(service="matchmaking_service")
        assert len(logs) == 1
        assert logs[0]["metadata"]["room_id"] == "room_123"

    asyncio.run(_test())


def test_metrics_collector_counters_gauges_histograms():
    metrics = MetricsCollector()

    # Counters
    val1 = metrics.increment_counter("http_requests_total", 1.0, labels={"endpoint": "/login"})
    val2 = metrics.increment_counter("http_requests_total", 2.0, labels={"endpoint": "/login"})
    assert val2 == 3.0

    # Gauges
    metrics.set_gauge("active_connections", 42.0, labels={"gateway": "ws_1"})
    json_data = metrics.to_json()
    assert json_data["gauges"]["active_connections"]['gateway="ws_1"'] == 42.0

    # Histograms
    metrics.observe_histogram("move_latency_ms", 12.5)
    metrics.observe_histogram("move_latency_ms", 25.0)
    metrics.observe_histogram("move_latency_ms", 18.0)

    prom_text = metrics.to_prometheus()
    assert "service_uptime_seconds" in prom_text
    assert "http_requests_total" in prom_text
    assert "active_connections" in prom_text
    assert "move_latency_ms" in prom_text


def test_cluster_health_checker_probes():
    async def _test():
        checker = ClusterHealthChecker()

        async def mock_http(name, url):
            return {"status": "ok", "latency_ms": 2.5}

        async def mock_redis():
            return {"status": "ok", "latency_ms": 1.0}

        async def mock_postgres():
            return {"status": "ok", "latency_ms": 3.0}

        async def mock_nats(bus=None):
            return {"status": "ok", "latency_ms": 0.5}

        with patch.object(checker, "check_http_endpoint", side_effect=mock_http), \
             patch.object(checker, "check_redis", side_effect=mock_redis), \
             patch.object(checker, "check_postgres", side_effect=mock_postgres), \
             patch.object(checker, "check_nats", side_effect=mock_nats):

            report = await checker.run_full_system_check()
            assert report["status"] == "HEALTHY"
            assert report["healthy_components"] == 5
            assert report["components"]["postgres"]["status"] == "ok"

    asyncio.run(_test())


def test_load_tester_execution():
    async def _test():
        tester = LoadTester()

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = b'{"status":"ok"}'
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            res = await tester.run_load_test(num_users=2, duration_seconds=0.2, target_url="http://localhost:8000")
            assert res["num_users"] == 2
            assert res["total_requests"] > 0
            assert res["successful_requests"] == res["total_requests"]
            assert res["requests_per_second"] >= 0
            assert tester.status == "completed"

    asyncio.run(_test())


def test_observability_fastapi_endpoints():
    async def _test():
        # /healthz
        res = await health_check()
        assert res.service == "observability_service"

        # /metrics/record
        rec_res = await record_metric(RecordMetricRequest(
            metric_type="counter",
            name="test_counter",
            value=5,
            labels={"env": "test"}
        ))
        assert rec_res["status"] == "success"

        # /metrics
        prom_res = await get_prometheus_metrics()
        assert "test_counter" in prom_res

        # /metrics/json
        json_res = await get_json_metrics()
        assert "counters" in json_res

        # /logs
        ingest_res = await ingest_log(LogIngestRequest(
            service="test_service",
            level="INFO",
            message="Testing observability log endpoint"
        ))
        assert ingest_res["status"] == "success"

        q_res = await query_logs(service="test_service", level="INFO", search=None, limit=100)
        assert q_res["count"] == 1

        # /load-test/status & results
        status_res = await get_load_test_status()
        assert "status" in status_res

        results_res = await get_load_test_results()
        assert "status" in results_res

    asyncio.run(_test())

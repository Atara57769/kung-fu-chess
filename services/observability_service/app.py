import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from shared.constants import ResponseStatus
from shared.message_contracts.contracts import HealthStatusPayload
from shared.message_contracts.nats_client import NatsBus
from services.observability_service import config
from services.observability_service.logs import LogCollector
from services.observability_service.metrics import MetricsCollector, MetricType
from services.observability_service.health import ClusterHealthChecker
from services.observability_service.load_test import LoadTester

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] ObservabilityService: %(message)s")
logger = logging.getLogger("ObservabilityService")

log_collector = LogCollector(max_entries=config.MAX_LOG_ENTRIES)
metrics_collector = MetricsCollector()
health_checker = ClusterHealthChecker()
load_tester = LoadTester()
nats_bus = NatsBus(url=config.NATS_URL)


class LogIngestRequest(BaseModel):
    service: str
    level: str = "INFO"
    message: str
    metadata: Optional[Dict[str, Any]] = None


class RecordMetricRequest(BaseModel):
    metric_type: MetricType = MetricType.COUNTER
    name: str
    value: float = 1.0
    labels: Optional[Dict[str, str]] = None



class LoadTestRequest(BaseModel):
    num_users: int = Field(default=10, ge=1, le=500)
    duration_seconds: float = Field(default=5.0, ge=1.0, le=300.0)
    target_url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages background tasks and NATS event stream listener."""
    try:
        await nats_bus.connect()
        logger.info("Observability Service NATS connection established.")
        await nats_bus.subscribe("system.logs", log_collector.handle_nats_log_event)
    except Exception as e:
        logger.warning("NATS connection not ready on Observability startup: %s", e)

    yield

    try:
        await nats_bus.close()
    except Exception:
        pass

app = FastAPI(
    title="Kung-Fu Chess Observability Service",
    description="Centralized Microservice for Logs, Prometheus Metrics, System Health Checks, and Load Testing",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/healthz", response_model=None)
async def health_check() -> HealthStatusPayload:
    """Self-health status check for Observability Service."""
    return HealthStatusPayload(status=ResponseStatus.OK.value, service="observability_service")


@app.get("/health/system")
async def system_cluster_health():
    """Returns composite cluster health status by probing all backend services and infrastructure components."""
    report = await health_checker.run_full_system_check(nats_bus)
    return report


@app.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """Exposes system metrics in standard Prometheus text exposition format."""
    return metrics_collector.to_prometheus()


@app.get("/metrics/json")
async def get_json_metrics():
    """Returns JSON representation of all collected counters, gauges, and histograms."""
    return metrics_collector.to_json()


@app.post("/metrics/record")
async def record_metric(req: RecordMetricRequest):
    """Records custom metric data (counter increment, gauge value, or histogram observation)."""
    metrics_collector.record_metric(
        metric_type=req.metric_type,
        name=req.name,
        value=req.value,
        labels=req.labels
    )
    return {"status": "success", "recorded": req.model_dump()}


@app.get("/logs")
async def query_logs(
    service: Optional[str] = Query(None, description="Filter by service name"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARN, ERROR, DEBUG)"),
    search: Optional[str] = Query(None, description="Search keyword in message"),
    limit: int = Query(100, ge=1, le=1000, description="Max entries to return")
):
    """Queries stored logs using service name, log level, or search keywords."""
    entries = log_collector.query_logs(service=service, level=level, search=search, limit=limit)
    return {"count": len(entries), "logs": entries}


@app.post("/logs")
async def ingest_log(req: LogIngestRequest):
    """Ingests a structured log entry into the centralized log buffer."""
    entry = log_collector.ingest_log(
        service=req.service,
        level=req.level,
        message=req.message,
        metadata=req.metadata
    )
    return {"status": "success", "entry": entry}


@app.post("/load-test/run")
async def run_load_test(req: LoadTestRequest):
    """Triggers a synthetic load test with specified virtual users and test duration."""
    if load_tester.status == "running":
        raise HTTPException(status_code=409, detail="A load test is already currently running.")

    # Execute inline / async task
    result = await load_tester.run_load_test(
        num_users=req.num_users,
        duration_seconds=req.duration_seconds,
        target_url=req.target_url
    )
    return {"status": "completed", "result": result}


@app.get("/load-test/status")
async def get_load_test_status():
    """Gets the execution status of the load testing engine."""
    return {"status": load_tester.status}


@app.get("/load-test/results")
async def get_load_test_results():
    """Retrieves results of the most recent load test."""
    if not load_tester.latest_result:
        return {"status": "no_results", "result": None}
    return {"status": "success", "result": load_tester.latest_result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.observability_service.app:app", host="0.0.0.0", port=config.PORT, reload=False)

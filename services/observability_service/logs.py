import time
import logging
from collections import deque
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ObservabilityService.Logs")


class LogCollector:
    """Bounded in-memory ring-buffer for centralized log ingestion and querying."""

    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.logs: deque = deque(maxlen=max_entries)

    def ingest_log(
        self,
        service: str,
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Ingests a structured log entry into memory."""
        entry = {
            "timestamp": timestamp or time.time(),
            "service": service,
            "level": level.upper(),
            "message": message,
            "metadata": metadata or {}
        }
        self.logs.append(entry)
        return entry

    def query_logs(
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Queries stored logs filtering by service, level, and keyword search."""
        results = []
        for entry in reversed(self.logs):
            if service and entry["service"].lower() != service.lower():
                continue
            if level and entry["level"] != level.upper():
                continue
            if search and search.lower() not in entry["message"].lower():
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results

    def clear(self) -> None:
        """Clears all stored logs."""
        self.logs.clear()

    async def handle_nats_log_event(self, data: Dict[str, Any], reply_to: Optional[str] = None) -> None:
        """NATS callback handler for log messages broadcast on system.logs topic."""
        try:
            if isinstance(data, dict):
                service = data.get("service", "unknown")
                level = data.get("level", "INFO")
                message = data.get("message", "")
                metadata = data.get("metadata", {})
                timestamp = data.get("timestamp")
                self.ingest_log(service, level, message, metadata, timestamp)
        except Exception as e:
            logger.error("Failed to process NATS log event: %s", e)

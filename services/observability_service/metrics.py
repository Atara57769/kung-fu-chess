import time
import math
from enum import Enum
from typing import Dict, Any, List, Optional, Union


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class MetricsCollector:

    """Metrics Collector supporting counters, gauges, histograms, and Prometheus/JSON export."""

    def __init__(self):
        self.start_time = time.time()
        self.counters: Dict[str, Dict[str, float]] = {}
        self.gauges: Dict[str, Dict[str, float]] = {}
        self.histograms: Dict[str, Dict[str, List[float]]] = {}

    def _format_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return ""
        items = sorted(labels.items())
        return ",".join(f'{k}="{v}"' for k, v in items)

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> float:
        """Increments a counter metric by value."""
        if name not in self.counters:
            self.counters[name] = {}
        key = self._format_label_key(labels)
        current = self.counters[name].get(key, 0.0)
        self.counters[name][key] = current + value
        return self.counters[name][key]

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> float:
        """Sets a gauge metric to a given value."""
        if name not in self.gauges:
            self.gauges[name] = {}
        key = self._format_label_key(labels)
        self.gauges[name][key] = value
        return value

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Applies a sample value to a histogram metric."""
        if name not in self.histograms:
            self.histograms[name] = {}
        key = self._format_label_key(labels)
        if key not in self.histograms[name]:
            self.histograms[name][key] = []
        self.histograms[name][key].append(value)
        if len(self.histograms[name][key]) > 5000:
            self.histograms[name][key] = self.histograms[name][key][-2500:]

    def record_metric(
        self,
        metric_type: Union[MetricType, str],
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Generic recorder supporting 'counter', 'gauge', or 'histogram'."""
        mtype = metric_type.value if isinstance(metric_type, MetricType) else str(metric_type).lower()
        if mtype == MetricType.COUNTER.value:
            self.increment_counter(name, value, labels)
        elif mtype == MetricType.GAUGE.value:
            self.set_gauge(name, value, labels)
        elif mtype == MetricType.HISTOGRAM.value:
            self.observe_histogram(name, value, labels)


    def to_json(self) -> Dict[str, Any]:
        """Returns JSON representation of all collected metrics."""
        uptime = time.time() - self.start_time
        hist_stats = {}
        for h_name, label_map in self.histograms.items():
            hist_stats[h_name] = {}
            for label_key, values in label_map.items():
                if not values:
                    continue
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                p95_idx = int(math.ceil(0.95 * n)) - 1
                hist_stats[h_name][label_key] = {
                    "count": n,
                    "min": sorted_vals[0],
                    "max": sorted_vals[-1],
                    "mean": sum(sorted_vals) / n,
                    "p95": sorted_vals[max(0, p95_idx)]
                }

        return {
            "uptime_seconds": uptime,
            "counters": self.counters,
            "gauges": self.gauges,
            "histograms": hist_stats
        }

    def to_prometheus(self) -> str:
        """Formats metrics into Prometheus text exposition format."""
        lines: List[str] = [
            "# HELP service_uptime_seconds Total runtime of the service in seconds.",
            "# TYPE service_uptime_seconds gauge",
            f"service_uptime_seconds {time.time() - self.start_time:.3f}"
        ]

        # Counters
        for c_name, label_map in self.counters.items():
            lines.append(f"# HELP {c_name} Counter metric.")
            lines.append(f"# TYPE {c_name} counter")
            for label_key, val in label_map.items():
                lbl_str = f"{{{label_key}}}" if label_key else ""
                lines.append(f"{c_name}{lbl_str} {val}")

        # Gauges
        for g_name, label_map in self.gauges.items():
            lines.append(f"# HELP {g_name} Gauge metric.")
            lines.append(f"# TYPE {g_name} gauge")
            for label_key, val in label_map.items():
                lbl_str = f"{{{label_key}}}" if label_key else ""
                lines.append(f"{g_name}{lbl_str} {val}")

        # Histograms
        for h_name, label_map in self.histograms.items():
            lines.append(f"# HELP {h_name} Histogram metric.")
            lines.append(f"# TYPE {h_name} summary")
            for label_key, values in label_map.items():
                if not values:
                    continue
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                p95_idx = int(math.ceil(0.95 * n)) - 1
                base_lbl = f"{label_key}," if label_key else ""
                lines.append(f'{h_name}_count{{{label_key}}} {n}')
                lines.append(f'{h_name}_sum{{{label_key}}} {sum(sorted_vals)}')
                lines.append(f'{h_name}{{{base_lbl}quantile="0.95"}} {sorted_vals[max(0, p95_idx)]}')

        return "\n".join(lines) + "\n"

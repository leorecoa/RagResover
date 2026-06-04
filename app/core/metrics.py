from collections import defaultdict
from threading import Lock


class RequestMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._duration_sum: dict[tuple[str, str], float] = defaultdict(float)

    def record(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        method = method.upper()
        with self._lock:
            self._requests[(method, path, int(status_code))] += 1
            self._duration_sum[(method, path)] += duration_ms / 1000

    def render_prometheus(self) -> str:
        lines = [
            "# HELP ragresover_http_requests_total Total HTTP requests.",
            "# TYPE ragresover_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status_code), count in sorted(self._requests.items()):
                lines.append(
                    "ragresover_http_requests_total"
                    f'{{method="{method}",path="{path}",status_code="{status_code}"}} {count}'
                )

            lines.extend(
                [
                    "# HELP ragresover_http_request_duration_seconds_sum Total HTTP request duration.",
                    "# TYPE ragresover_http_request_duration_seconds_sum counter",
                ]
            )
            for (method, path), duration in sorted(self._duration_sum.items()):
                lines.append(
                    "ragresover_http_request_duration_seconds_sum"
                    f'{{method="{method}",path="{path}"}} {duration:.6f}'
                )

        return "\n".join(lines) + "\n"


request_metrics = RequestMetrics()

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request, Response
import time

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "path", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["service", "method", "path"]
)

def metrics_middleware(service_name: str):
    async def middleware(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        REQUEST_COUNT.labels(
            service=service_name,
            method=request.method,
            path=request.url.path,
            status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            service=service_name,
            method=request.method,
            path=request.url.path
        ).observe(duration)

        return response

    return middleware

def metrics_endpoint():
    return Response(
        generate_latest(),
        media_type="text/plain"
    )

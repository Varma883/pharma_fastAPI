# Pharma FastAPI Project — Demo Guide

This guide describes how to showcase the advanced features of the Pharma FastAPI project: **Load Balancing, Circuit Breaking, Redis Caching, Rate Limiting, and Observability.**

## Prerequisites
Ensure all services are running:
```bash
docker-compose up -d --build
```

---

## 1. Load Balancing (Nginx + Replicas)
**Goal:** Show traffic being distributed between `catalog_service` and `catalog_service_replica`.

1.  **Open Postman** (or browser) to: `http://localhost:8000/catalog/`
2.  **Send Request** multiple times (e.g., 4-5 times).
3.  **Observe**: Look at the response JSON.
    *   The `hostname` field will change between two different IDs (e.g., `a1b2c3d4e5f6` and `f6e5d4c3b2a1`).
    *   This proves that **Nginx** is successfully balancing requests between the two containers.

## 2. API Gateway & Routing (Kong)
**Goal:** Show how Kong routes traffic and rewrites URLs.

1.  **Request**: `http://localhost:8000/catalog/drugs`
    *   Kong receives this on port `8000`.
    *   It strips `/catalog` and forwards `/drugs` to the internal upstream.
2.  **Request**: `http://localhost:8000/inventory/health`
    *   Kong forwards `/inventory` as-is to the Inventory Service.
    *   This demonstrates **Path-Based Routing**.

## 3. Rate Limiting (Kong)
**Goal:** Show the system protecting itself from flood attacks.

1.  **Tool**: Use Postman Runner or a simple script.
2.  **Config**: The limit is set to **100 requests per minute**.
3.  **Action**: Send 110 requests to `http://localhost:8000/catalog/` in quick succession.
4.  **Result**:
    *   Requests 1-100: **200 OK**
    *   Request 101+: **429 Too Many Requests**
    *   Error message: `"API rate limit exceeded"`

## 4. Redis Caching & Resilience
**Goal:** Show `orders_service` surviving an outage of `inventory_service` by using Redis Cache.

1.  **Prime the Cache**:
    *   Call `GET http://localhost:8000/orders/check-inventory/1` (Token required).
    *   Response: `{"quantity": 100, "source": "service"}`.
    *   *This fetches data from Inventory Service and saves it to Redis.*
2.  **Simulate Outage**:
    *   Stop the inventory container:
        ```bash
        docker stop inventory_service
        ```
3.  **Verify Resilience**:
    *   Call `GET http://localhost:8000/orders/check-inventory/1` again.
    *   Response: `{"quantity": 100, "source": "redis_cache"}`.
    *   **Result**: The system **did not fail** despite the backend service being down.
4.  **Recover**:
    *   Start the service back up: `docker start inventory_service`.

## 5. Circuit Breaker (Custom Implementation)
**Goal:** Show `inventory_service` failing fast when `catalog_service` is down.

1.  **Action**: Call the explicit test endpoint:
    *   `GET http://localhost:8000/inventory/test-circuit-breaker`
2.  **Result**:
    *   **First 5 hits**: The requests will hang slightly (timeout) and return `503 Service Unavailable`. *This is the breaker counting failures.*
    *   **6th hit**: Returns **IMMEDIATELY** with `503 Circuit breaker open`.
    *   *This proves the system stopped trying to connect to the dead service to save resources.*

## 6. Observability (Prometheus & Grafana)
**Goal:** Visualize the metrics generated during the steps above.

1.  **Grafana**: Open `http://localhost:3000` (admin/admin).
2.  **Dashboard**: Go to **Dashboards > General > FastApi Observability**.
3.  **Real-time Updates**:
    *   While performing the **Rate Limiting** test (Step 3), watch the **Requests per Second** graph spike.
    *   While performing **Circuit Breaker** test (Step 5), watch the **5xx Errors** graph spike.

---
**Note on Authentication**:
Most endpoints require a JWT token.
1.  **Register**: `POST /auth/register`
2.  **Login**: `POST /auth/login` -> Copy `access_token`.
3.  **Use**: Add header `Authorization: Bearer <token>` for subsequent requests.

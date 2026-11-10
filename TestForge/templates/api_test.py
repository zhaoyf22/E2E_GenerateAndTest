"""TestForge API test skeleton (pytest + httpx).

Rules:
- Assert status + schema + business fields, not just 200.
- Use fixtures for auth/data; unique values; cleanup.
- Cover error codes, auth, idempotency, state transitions.
"""
from __future__ import annotations

import uuid

import httpx
import pytest


@pytest.fixture()
def client() -> httpx.Client:
    with httpx.Client(base_url="http://localhost:8000", timeout=10.0) as c:
        yield c


@pytest.fixture()
def auth_headers(client: httpx.Client) -> dict[str, str]:
    email = f"buyer+{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/test/seed", json={"email": email})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_create_order_success(client: httpx.Client, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/orders",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"sku": "SKU-001", "qty": 1},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_payment"
    assert body["sku"] == "SKU-001"
    assert body["qty"] == 1
    assert "order_id" in body


def test_create_order_stock_insufficient(client: httpx.Client, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/orders",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"sku": "SKU-001", "qty": 9999},
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "STOCK_INSUFFICIENT"


def test_create_order_requires_auth(client: httpx.Client) -> None:
    response = client.post("/orders", json={"sku": "SKU-001", "qty": 1})

    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED"


def test_create_order_is_idempotent(client: httpx.Client, auth_headers: dict[str, str]) -> None:
    key = str(uuid.uuid4())
    payload = {"sku": "SKU-001", "qty": 1}

    first = client.post("/orders", headers={**auth_headers, "Idempotency-Key": key}, json=payload)
    second = client.post("/orders", headers={**auth_headers, "Idempotency-Key": key}, json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["order_id"] == second.json()["order_id"]

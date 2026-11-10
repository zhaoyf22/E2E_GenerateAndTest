"""TestForge pytest skeleton.

Rules:
- Mock external dependencies; no real network unless marked integration.
- Assert behavior/contract, not private implementation.
- Each test owns its data; fixed seed; cleanup.
"""
from __future__ import annotations

import pytest

from app.orders import OrderService, StockInsufficient


class FakeStock:
    def __init__(self, stock: int) -> None:
        self.stock = stock

    def available(self, sku: str) -> int:
        return self.stock

    def deduct(self, sku: str, qty: int) -> None:
        if qty > self.stock:
            raise StockInsufficient(sku)
        self.stock -= qty


@pytest.fixture()
def service() -> OrderService:
    return OrderService(stock=FakeStock(1), orders=[])


def test_create_order_when_stock_is_enough(service: OrderService) -> None:
    order = service.create(sku="SKU-001", qty=1, buyer="buyer+001@example.com")

    assert order.status == "pending_payment"
    assert service.stock.available("SKU-001") == 0
    assert service.orders == [order]


@pytest.mark.parametrize("qty", [2, 10])
def test_reject_order_when_stock_is_insufficient(service: OrderService, qty: int) -> None:
    with pytest.raises(StockInsufficient):
        service.create(sku="SKU-001", qty=qty, buyer="buyer+001@example.com")

    assert service.stock.available("SKU-001") == 1
    assert service.orders == []


def test_reject_qty_zero(service: OrderService) -> None:
    with pytest.raises(ValueError):
        service.create(sku="SKU-001", qty=0, buyer="buyer+001@example.com")

    assert service.stock.available("SKU-001") == 1

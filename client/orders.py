"""Delivery orders and a thread-safe priority queue.

Urgent orders (e.g. ICU / emergency medicine) are served before normal
ones; orders with the same priority are served first-come-first-served.
"""

from __future__ import annotations

import heapq
import itertools
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional

PRIORITY_URGENT = 0
PRIORITY_NORMAL = 1
PRIORITY_NAMES = {PRIORITY_URGENT: "URGENT", PRIORITY_NORMAL: "normal"}


@dataclass
class Order:
    order_id: int
    pickup: str
    dropoff: str
    priority: int = PRIORITY_NORMAL
    item: str = "package"
    status: str = "queued"            # queued | running | done | failed | cancelled
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    plan_time_s: float = 0.0          # total time spent in the planner
    path_length_m: float = 0.0        # total planned path length
    note: str = ""

    def summary(self) -> str:
        return (f"#{self.order_id:<3} {PRIORITY_NAMES[self.priority]:<6} "
                f"{self.item:<10} {self.pickup:>10} -> {self.dropoff:<10} {self.status}"
                + (f" ({self.note})" if self.note else ""))


class OrderQueue:
    def __init__(self) -> None:
        self._heap: list = []
        self._seq = itertools.count()
        self._ids = itertools.count(1)
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self.history: List[Order] = []   # every order ever created

    def add(self, pickup: str, dropoff: str, priority: int = PRIORITY_NORMAL,
            item: str = "package") -> Order:
        with self._lock:
            order = Order(next(self._ids), pickup, dropoff, priority, item)
            heapq.heappush(self._heap, (priority, next(self._seq), order))
            self.history.append(order)
            self._not_empty.notify()
            return order

    def pop(self, timeout: Optional[float] = None) -> Optional[Order]:
        """Next order to serve (skipping cancelled ones), or None on timeout."""
        with self._not_empty:
            end = None if timeout is None else time.time() + timeout
            while True:
                while self._heap:
                    _, _, order = heapq.heappop(self._heap)
                    if order.status == "queued":
                        return order
                remaining = None if end is None else end - time.time()
                if remaining is not None and remaining <= 0:
                    return None
                self._not_empty.wait(remaining)

    def cancel(self, order_id: int) -> bool:
        with self._lock:
            for order in self.history:
                if order.order_id == order_id and order.status == "queued":
                    order.status = "cancelled"
                    return True
            return False

    def pending(self) -> List[Order]:
        with self._lock:
            items = sorted(self._heap)
            return [o for _, _, o in items if o.status == "queued"]

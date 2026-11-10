"""Background worker that takes orders from the queue and executes them:

    current position -> pickup -> dropoff

It plans each leg with the planner, drives it with the bridge, and logs the
result (planning time, path length, total time) to a CSV for the Results
section.
"""

from __future__ import annotations

import csv
import os
import threading
import time
from typing import Dict, Optional, Tuple

from . import config
from .interfaces import load_planner, path_length
from .orders import PRIORITY_NAMES, Order, OrderQueue

Point = Tuple[float, float]

CSV_FIELDS = ["order_id", "priority", "item", "pickup", "dropoff", "status",
              "wait_s", "run_s", "plan_time_s", "path_length_m", "note"]


class Dispatcher(threading.Thread):
    def __init__(self, queue: OrderQueue, bridge, log_csv: str = config.ORDER_LOG_CSV):
        super().__init__(daemon=True)
        self.queue = queue
        self.bridge = bridge
        self.log_csv = log_csv
        self.plan, self.planner_name = load_planner()
        self.locations: Dict[str, Point] = dict(config.LOCATIONS)

        self.current: Optional[Order] = None
        self.last_pose = (0.0, 0.0, 0.0)
        self.ready = threading.Event()        # set once connected
        self.error: Optional[str] = None
        self._estop = threading.Event()       # emergency stop / pause
        self._estop_at = 0.0
        self._quit = threading.Event()
        self._last_pose_update = 0.0

    # ---- commands from the shell (thread-safe) ----
    def emergency_stop(self) -> None:
        if not self._estop.is_set():
            self._estop_at = time.perf_counter()
        self._estop.set()

    def resume(self) -> None:
        self._estop.clear()

    @property
    def stopped(self) -> bool:
        return self._estop.is_set()

    def shutdown(self) -> None:
        self._quit.set()

    # ---- worker thread ----
    def run(self) -> None:
        try:
            self.bridge.connect()
            self.locations.update(self.bridge.scene_locations())
            self.last_pose = self.bridge.pose()
        except Exception as e:  # report to the shell instead of crashing
            self.error = str(e)
            self.ready.set()
            return
        self.ready.set()

        while not self._quit.is_set():
            if self._estop.is_set():
                time.sleep(0.1)
                continue
            order = self.queue.pop(timeout=0.2)
            if order is None:
                self.last_pose = self.bridge.pose()
                continue
            self._execute(order)
        self.bridge.close()

    def _should_stop(self) -> bool:
        # Called by the follower every control step (in this thread), so it is
        # also a safe place to refresh the pose shown by `status`.
        now = time.perf_counter()
        if now - self._last_pose_update > 0.3:
            self._last_pose_update = now
            try:
                self.last_pose = self.bridge.pose()
            except Exception:
                pass
        return self._estop.is_set() or self._quit.is_set()

    def _leg(self, order: Order, goal_name: str) -> bool:
        x, y, _ = self.bridge.pose()
        goal = self.locations[goal_name]
        t0 = time.perf_counter()
        path = self.plan((x, y), goal)
        order.plan_time_s += time.perf_counter() - t0
        if not path:
            order.note = f"no path to {goal_name}"
            return False
        order.path_length_m += path_length(path)
        ok = self.bridge.drive(path, self._should_stop)
        self.last_pose = self.bridge.pose()
        if not ok:
            if self._estop.is_set():
                latency = time.perf_counter() - self._estop_at
                order.note = f"emergency stop, halted in {latency:.2f} s"
            elif self._quit.is_set():
                order.note = "client quit"
            else:
                order.note = f"failed to reach {goal_name}"
        return ok

    def _execute(self, order: Order) -> None:
        self.current = order
        order.status, order.started_at = "running", time.time()
        ok = self._leg(order, order.pickup) and self._leg(order, order.dropoff)
        order.status = "done" if ok else "failed"
        order.finished_at = time.time()
        self.current = None
        self._log(order)
        print(f"\n[robot] order #{order.order_id} {order.status}"
              f" ({order.pickup} -> {order.dropoff}, {order.path_length_m:.1f} m"
              f"{', ' + order.note if order.note else ''})\nhospital> ", end="", flush=True)

    def _log(self, order: Order) -> None:
        os.makedirs(os.path.dirname(self.log_csv) or ".", exist_ok=True)
        new = not os.path.exists(self.log_csv)
        with open(self.log_csv, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if new:
                w.writeheader()
            w.writerow({
                "order_id": order.order_id,
                "priority": PRIORITY_NAMES[order.priority],
                "item": order.item,
                "pickup": order.pickup,
                "dropoff": order.dropoff,
                "status": order.status,
                "wait_s": round(order.started_at - order.created_at, 3),
                "run_s": round(order.finished_at - order.started_at, 3),
                "plan_time_s": round(order.plan_time_s, 4),
                "path_length_m": round(order.path_length_m, 3),
                "note": order.note,
            })

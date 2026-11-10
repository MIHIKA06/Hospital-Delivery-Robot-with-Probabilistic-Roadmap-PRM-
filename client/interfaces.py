"""Glue between the client and teammates' modules.

AGREED INTERFACES (do not change without telling the team):

  planner/prm.py          (Disha)
      def plan(start: tuple[float, float], goal: tuple[float, float])
              -> list[tuple[float, float]] | None
      Returns waypoints from start to goal (inclusive), or None if no path.

  controller/controller.py (Sumit)
      def follow(sim, robot_handle, path, should_stop) -> bool
      Drives the robot along `path` in CoppeliaSim. `should_stop()` returns
      True when the client wants an emergency stop. Returns True on arrival.

Until those files exist, simple fallbacks below are used so the client can be
developed and demonstrated on its own.
"""

from __future__ import annotations

import math
import time
from typing import Callable, List, Optional, Sequence, Tuple

Point = Tuple[float, float]


def path_length(path: Sequence[Point]) -> float:
    return sum(math.dist(a, b) for a, b in zip(path, path[1:]))


def _straight_line_plan(start: Point, goal: Point) -> List[Point]:
    """Fallback planner: straight line (ignores obstacles!)."""
    return [tuple(start), tuple(goal)]


def load_planner() -> Tuple[Callable[[Point, Point], Optional[List[Point]]], str]:
    try:
        from planner.prm import plan  # type: ignore
        return plan, "PRM (planner/prm.py)"
    except ImportError:
        return _straight_line_plan, "FALLBACK straight-line planner (planner/prm.py not found)"


def _kinematic_follow(sim, robot_handle, path, should_stop, speed=0.8, dt=0.05) -> bool:
    """Fallback follower: moves the robot model directly along the path
    (no physics/controller). Good enough to test the client end to end."""
    for a, b in zip(path, path[1:]):
        dist = math.dist(a, b)
        steps = max(1, int(dist / (speed * dt)))
        heading = math.atan2(b[1] - a[1], b[0] - a[0])
        z = sim.getObjectPosition(robot_handle, sim.handle_world)[2]
        for i in range(1, steps + 1):
            if should_stop():
                return False
            t = i / steps
            sim.setObjectPosition(robot_handle, sim.handle_world,
                                  [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), z])
            sim.setObjectOrientation(robot_handle, sim.handle_world, [0, 0, heading])
            time.sleep(dt)
    return True


def load_follower():
    try:
        from controller.controller import follow  # type: ignore
        return follow, "PID controller (controller/controller.py)"
    except ImportError:
        return _kinematic_follow, "FALLBACK kinematic follower (controller/controller.py not found)"

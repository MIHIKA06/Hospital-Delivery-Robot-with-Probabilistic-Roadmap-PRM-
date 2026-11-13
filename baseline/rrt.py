"""Rapidly-exploring Random Tree (RRT) path planner baseline.

Used as the baseline single-query planner to compare against the multi-query
Probabilistic Roadmap (PRM) planner in the hospital floor plan.

Author: Divyanshu Dhyani (M2)
Module: baseline/
"""

from __future__ import annotations

import math
import random
import time
from typing import Dict, List, Optional, Sequence, Tuple

from planner import hospital_map as hm
from planner.prm import edge_free, inflate, point_free

Point = Tuple[float, float]
Rect = Tuple[float, float, float, float]


class RRT:
    """Goal-biased 2D Rapidly-exploring Random Tree (RRT) planner."""

    def __init__(
        self,
        obstacles: Sequence[Rect] = hm.OBSTACLES,
        bounds: Rect = hm.BOUNDS,
        robot_radius: float = hm.ROBOT_RADIUS,
        step_size: float = 0.40,
        goal_bias: float = 0.15,
        max_iter: int = 3500,
        seed: Optional[int] = 42,
    ):
        self.obstacles = list(obstacles)
        self.bounds = bounds
        self.r = robot_radius
        self.cobs = inflate(self.obstacles, self.r)
        self.step_size = step_size
        self.goal_bias = goal_bias
        self.max_iter = max_iter
        self.rng = random.Random(seed)

        # Diagnostics from last query
        self.last_query_time_s: float = 0.0
        self.last_iterations: int = 0
        self.last_tree_size: int = 0

    def _sample(self, goal: Point) -> Point:
        """Sample a target configuration with goal-biasing."""
        if self.rng.random() < self.goal_bias:
            return goal
        return (
            self.rng.uniform(self.bounds[0], self.bounds[2]),
            self.rng.uniform(self.bounds[1], self.bounds[3]),
        )

    def _nearest_node(self, nodes: List[Point], target: Point) -> int:
        """Find index of the tree node closest to target."""
        best_idx = 0
        best_dist = math.dist(nodes[0], target)
        for i in range(1, len(nodes)):
            d = math.dist(nodes[i], target)
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx

    def _steer(self, from_pt: Point, to_pt: Point) -> Point:
        """Step along ray towards to_pt by at most step_size."""
        d = math.dist(from_pt, to_pt)
        if d <= self.step_size:
            return to_pt
        ratio = self.step_size / d
        return (
            from_pt[0] + ratio * (to_pt[0] - from_pt[0]),
            from_pt[1] + ratio * (to_pt[1] - from_pt[1]),
        )

    def query(self, start: Point, goal: Point, smooth: bool = True) -> Optional[List[Point]]:
        """Plan a path from start to goal using RRT."""
        t0 = time.perf_counter()
        start, goal = tuple(start), tuple(goal)

        if not (point_free(start, self.cobs, self.bounds) and point_free(goal, self.cobs, self.bounds)):
            self.last_query_time_s = time.perf_counter() - t0
            return None

        # Direct line-of-sight shortcut
        if edge_free(start, goal, self.cobs):
            self.last_query_time_s = time.perf_counter() - t0
            self.last_iterations = 0
            self.last_tree_size = 2
            return [start, goal]

        nodes: List[Point] = [start]
        parent: Dict[int, int] = {0: -1}

        success = False
        goal_idx = -1

        for it in range(self.max_iter):
            rnd = self._sample(goal)
            nearest_idx = self._nearest_node(nodes, rnd)
            nearest_pt = nodes[nearest_idx]

            new_pt = self._steer(nearest_pt, rnd)

            if point_free(new_pt, self.cobs, self.bounds) and edge_free(nearest_pt, new_pt, self.cobs):
                new_idx = len(nodes)
                nodes.append(new_pt)
                parent[new_idx] = nearest_idx

                # Check if we can connect new_pt directly to goal
                dist_to_goal = math.dist(new_pt, goal)
                if dist_to_goal <= self.step_size * 1.5:
                    if edge_free(new_pt, goal, self.cobs):
                        goal_idx = len(nodes)
                        nodes.append(goal)
                        parent[goal_idx] = new_idx
                        success = True
                        self.last_iterations = it + 1
                        break

        self.last_tree_size = len(nodes)
        self.last_query_time_s = time.perf_counter() - t0

        if not success:
            return None

        # Reconstruct path
        path: List[Point] = []
        curr = goal_idx
        while curr != -1:
            path.append(nodes[curr])
            curr = parent[curr]
        path.reverse()

        return self.shortcut(path) if smooth else path

    def shortcut(self, path: List[Point]) -> List[Point]:
        """Greedy ray-cast shortcut smoothing (same as PRM for fair comparison)."""
        if len(path) <= 2:
            return path
        out: List[Point] = [path[0]]
        i = 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1 and not edge_free(path[i], path[j], self.cobs):
                j -= 1
            out.append(path[j])
            i = j
        return out

    def plan(self, start: Point, goal: Point) -> Optional[List[Point]]:
        """Compatible planning interface."""
        return self.query(start, goal, smooth=True)


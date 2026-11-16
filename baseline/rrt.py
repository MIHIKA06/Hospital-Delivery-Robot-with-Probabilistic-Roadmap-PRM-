"""Single-query RRT baseline (LaValle & Kuffner) for comparison with the PRM.

Each query grows a new tree from the start until it reaches the goal, so no
work is reused between orders. Uses the same map, robot radius and collision
checks as the PRM, so the comparison is fair.

    plan(start, goal) -> list[(x, y)] | None      (same interface as planner/prm.py)
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Tuple

from planner import hospital_map as hm
from planner.prm import edge_free, inflate, point_free

Point = Tuple[float, float]
Rect = Tuple[float, float, float, float]


class RRT:
    def __init__(self, obstacles: Sequence[Rect] = hm.OBSTACLES, bounds: Rect = hm.BOUNDS,
                 robot_radius: float = hm.ROBOT_RADIUS, step: float = 0.5,
                 goal_bias: float = 0.1, max_iters: int = 20000, seed: int = 1):
        self.cobs = inflate(obstacles, robot_radius)
        self.bounds = bounds
        self.step, self.goal_bias, self.max_iters = step, goal_bias, max_iters
        self.rng = random.Random(seed)
        self.last_iters = 0
        self.last_tree_size = 0

    def query(self, start: Point, goal: Point, smooth: bool = True) -> Optional[List[Point]]:
        start, goal = tuple(start), tuple(goal)
        if not (point_free(start, self.cobs, self.bounds) and point_free(goal, self.cobs, self.bounds)):
            return None
        nodes: List[Point] = [start]
        parent = [-1]
        for it in range(1, self.max_iters + 1):
            target = goal if self.rng.random() < self.goal_bias else (
                self.rng.uniform(self.bounds[0], self.bounds[2]),
                self.rng.uniform(self.bounds[1], self.bounds[3]))
            i_near = min(range(len(nodes)), key=lambda i: (nodes[i][0] - target[0]) ** 2
                         + (nodes[i][1] - target[1]) ** 2)
            near = nodes[i_near]
            d = math.dist(near, target)
            new = target if d <= self.step else (near[0] + (target[0] - near[0]) * self.step / d,
                                                 near[1] + (target[1] - near[1]) * self.step / d)
            if not edge_free(near, new, self.cobs):
                continue
            nodes.append(new)
            parent.append(i_near)
            if math.dist(new, goal) <= self.step and edge_free(new, goal, self.cobs):
                nodes.append(goal)
                parent.append(len(nodes) - 2)
                self.last_iters, self.last_tree_size = it, len(nodes)
                path, j = [], len(nodes) - 1
                while j != -1:
                    path.append(nodes[j])
                    j = parent[j]
                path.reverse()
                return self.shortcut(path) if smooth else path
        self.last_iters, self.last_tree_size = self.max_iters, len(nodes)
        return None

    def shortcut(self, path: List[Point]) -> List[Point]:
        out, i = [path[0]], 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1 and not edge_free(path[i], path[j], self.cobs):
                j -= 1
            out.append(path[j])
            i = j
        return out


_RRT = RRT()


def plan(start: Point, goal: Point) -> Optional[List[Point]]:
    return _RRT.query(start, goal)

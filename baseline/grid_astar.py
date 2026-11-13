"""Grid-based A* path planner baseline.

Used as a deterministic discrete-search baseline to compare against the
probabilistic PRM planner in the hospital floor plan.

Author: Divyanshu Dhyani (M2)
Module: baseline/
"""

from __future__ import annotations

import heapq
import math
import time
from typing import Dict, List, Optional, Sequence, Set, Tuple

from planner import hospital_map as hm
from planner.prm import edge_free, inflate, point_free

Point = Tuple[float, float]
Rect = Tuple[float, float, float, float]
GridIndex = Tuple[int, int]


class GridAStar:
    """8-connected 2D Grid A* path planner with obstacle inflation."""

    def __init__(
        self,
        obstacles: Sequence[Rect] = hm.OBSTACLES,
        bounds: Rect = hm.BOUNDS,
        robot_radius: float = hm.ROBOT_RADIUS,
        resolution: float = 0.20,
    ):
        self.obstacles = list(obstacles)
        self.bounds = bounds
        self.r = robot_radius
        self.cobs = inflate(self.obstacles, self.r)
        self.res = resolution

        # Grid dimensions
        self.x_min, self.y_min, self.x_max, self.y_max = self.bounds
        self.nx = int(math.ceil((self.x_max - self.x_min) / self.res))
        self.ny = int(math.ceil((self.y_max - self.y_min) / self.res))

        # Diagnostics
        self.last_query_time_s: float = 0.0
        self.last_nodes_expanded: int = 0

    def world_to_grid(self, pt: Point) -> GridIndex:
        gx = int(round((pt[0] - self.x_min) / self.res))
        gy = int(round((pt[1] - self.y_min) / self.res))
        return (max(0, min(self.nx - 1, gx)), max(0, min(self.ny - 1, gy)))

    def grid_to_world(self, idx: GridIndex) -> Point:
        x = self.x_min + idx[0] * self.res
        y = self.y_min + idx[1] * self.res
        return (x, y)

    def is_cell_free(self, idx: GridIndex) -> bool:
        if not (0 <= idx[0] < self.nx and 0 <= idx[1] < self.ny):
            return False
        pt = self.grid_to_world(idx)
        return point_free(pt, self.cobs, self.bounds)

    def query(self, start: Point, goal: Point, smooth: bool = True) -> Optional[List[Point]]:
        """Find path from start to goal on the discrete grid using A*."""
        t0 = time.perf_counter()
        start, goal = tuple(start), tuple(goal)

        if not (point_free(start, self.cobs, self.bounds) and point_free(goal, self.cobs, self.bounds)):
            self.last_query_time_s = time.perf_counter() - t0
            return None

        # Direct line-of-sight shortcut
        if edge_free(start, goal, self.cobs):
            self.last_query_time_s = time.perf_counter() - t0
            self.last_nodes_expanded = 0
            return [start, goal]

        start_cell = self.world_to_grid(start)
        goal_cell = self.world_to_grid(goal)

        # 8-connected movements: (dx, dy, cost)
        sqrt2 = math.sqrt(2) * self.res
        moves = [
            (1, 0, self.res), (-1, 0, self.res), (0, 1, self.res), (0, -1, self.res),
            (1, 1, sqrt2), (-1, 1, sqrt2), (1, -1, sqrt2), (-1, -1, sqrt2),
        ]

        def heuristic(cell: GridIndex) -> float:
            # Euclidean distance heuristic in world space
            cx, cy = self.grid_to_world(cell)
            return math.dist((cx, cy), goal)

        open_heap: List[Tuple[float, float, GridIndex]] = []
        heapq.heappush(open_heap, (heuristic(start_cell), 0.0, start_cell))

        g_cost: Dict[GridIndex, float] = {start_cell: 0.0}
        parent: Dict[GridIndex, GridIndex] = {}
        closed_set: Set[GridIndex] = set()

        expanded = 0
        reached = False

        while open_heap:
            f, current_g, current = heapq.heappop(open_heap)

            if current in closed_set:
                continue
            closed_set.add(current)
            expanded += 1

            if current == goal_cell:
                reached = True
                break

            for dx, dy, step_cost in moves:
                nbr: GridIndex = (current[0] + dx, current[1] + dy)

                if nbr in closed_set:
                    continue

                # Diagonal move check: prevent corner cutting
                if dx != 0 and dy != 0:
                    adj1 = (current[0] + dx, current[1])
                    adj2 = (current[0], current[1] + dy)
                    if not (self.is_cell_free(adj1) and self.is_cell_free(adj2)):
                        continue

                if not self.is_cell_free(nbr):
                    continue

                new_g = current_g + step_cost
                if new_g < g_cost.get(nbr, math.inf):
                    g_cost[nbr] = new_g
                    parent[nbr] = current
                    heapq.heappush(open_heap, (new_g + heuristic(nbr), new_g, nbr))

        self.last_nodes_expanded = expanded
        self.last_query_time_s = time.perf_counter() - t0

        if not reached:
            return None

        # Reconstruct path
        path_cells: List[GridIndex] = []
        curr = goal_cell
        while curr != start_cell:
            path_cells.append(curr)
            curr = parent[curr]
        path_cells.append(start_cell)
        path_cells.reverse()

        # Convert back to coordinates and append exact start & goal
        pts = [start] + [self.grid_to_world(c) for c in path_cells] + [goal]

        return self.shortcut(pts) if smooth else pts

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


"""Probabilistic Roadmap (PRM) planner for the hospital delivery robot.

Learning phase (once):  sample collision-free robot positions, connect each to
its k nearest neighbours with collision-free straight edges -> roadmap graph.
Query phase (per order): connect start and goal to the roadmap, run A*, then
shortcut-smooth the path.

The robot is a disc of radius r. Every obstacle rectangle is inflated by r
(configuration-space obstacle, conservatively as a box), so the robot is
treated as a point in C-space. Edge checks are exact segment-box tests.

Public interface used by the client (client/interfaces.py):
    plan(start, goal) -> list[(x, y)] | None
"""

from __future__ import annotations

import heapq
import math
import random
import threading
import time
from typing import Dict, List, Optional, Sequence, Tuple

from . import hospital_map as hm

Point = Tuple[float, float]
Rect = Tuple[float, float, float, float]


# --------------------------------------------------------------- geometry
def inflate(rects: Sequence[Rect], r: float) -> List[Rect]:
    return [(x0 - r, y0 - r, x1 + r, y1 + r) for x0, y0, x1, y1 in rects]


def point_free(p: Point, cobs: Sequence[Rect], bounds: Rect) -> bool:
    x, y = p
    if not (bounds[0] < x < bounds[2] and bounds[1] < y < bounds[3]):
        return False
    return not any(x0 < x < x1 and y0 < y < y1 for x0, y0, x1, y1 in cobs)


def segment_hits_box(a: Point, b: Point, box: Rect) -> bool:
    """Liang-Barsky clipping: does segment a-b pass through the open box?"""
    x0, y0, x1, y1 = box
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q <= 0:
                return False
        else:
            t = q / p
            if p < 0:
                if t > t1:
                    return False
                t0 = max(t0, t)
            else:
                if t < t0:
                    return False
                t1 = min(t1, t)
    return t1 - t0 > 1e-9


def edge_free(a: Point, b: Point, cobs: Sequence[Rect]) -> bool:
    return not any(segment_hits_box(a, b, box) for box in cobs)


# --------------------------------------------------------------- samplers
def sample_uniform(rng: random.Random, bounds: Rect) -> Point:
    return (rng.uniform(bounds[0], bounds[2]), rng.uniform(bounds[1], bounds[3]))


def sample_bridge(rng: random.Random, bounds: Rect, cobs, sigma: float = 0.6) -> Optional[Point]:
    """Bridge test (Hsu et al. 2003): two colliding points whose midpoint is free
    -> the midpoint lies in a narrow passage such as a doorway."""
    a = sample_uniform(rng, bounds)
    if point_free(a, cobs, bounds):
        return None
    b = (rng.gauss(a[0], sigma), rng.gauss(a[1], sigma))
    if point_free(b, cobs, bounds):
        return None
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return m if point_free(m, cobs, bounds) else None


def door_seeds(doors, offset: float = 0.6) -> List[Point]:
    """Door-seeded sampling (our variant): the floor plan tells us where the
    narrow passages are, so put one node in each doorway and one on each side."""
    pts = []
    for x, y, axis in doors:
        for d in (-offset, 0.0, offset):
            pts.append((x + d, y) if axis == "x" else (x, y + d))
    return pts


# --------------------------------------------------------------- PRM
class PRM:
    def __init__(self, obstacles: Sequence[Rect] = hm.OBSTACLES, bounds: Rect = hm.BOUNDS,
                 robot_radius: float = hm.ROBOT_RADIUS, n_samples: int = 300, k: int = 10,
                 max_edge: float = 3.0, sampler: str = "door", bridge_fraction: float = 0.3,
                 seed: int = 1):
        self.obstacles = list(obstacles)
        self.bounds = bounds
        self.r = robot_radius
        self.n_samples, self.k, self.max_edge = n_samples, k, max_edge
        self.sampler, self.bridge_fraction = sampler, bridge_fraction
        self.rng = random.Random(seed)
        self.cobs = inflate(self.obstacles, self.r)
        # C-space bounds: robot centre must stay r inside the outer walls
        self.nodes: List[Point] = []
        self.adj: Dict[int, Dict[int, float]] = {}
        self.build_time_s = 0.0

    # ---- learning phase
    def build(self) -> "PRM":
        t0 = time.perf_counter()
        if self.sampler == "door":
            self.nodes.extend(p for p in door_seeds(hm.DOORS)
                              if point_free(p, self.cobs, self.bounds))
        n_bridge = int(self.n_samples * self.bridge_fraction) if self.sampler == "bridge" else 0
        while len(self.nodes) < n_bridge:
            p = sample_bridge(self.rng, self.bounds, self.cobs)
            if p is not None:
                self.nodes.append(p)
        while len(self.nodes) < self.n_samples:
            p = sample_uniform(self.rng, self.bounds)
            if point_free(p, self.cobs, self.bounds):
                self.nodes.append(p)
        self.adj = {i: {} for i in range(len(self.nodes))}
        for i in range(len(self.nodes)):
            for j in self._neighbours(self.nodes[i], exclude=i):
                if j not in self.adj[i] and edge_free(self.nodes[i], self.nodes[j], self.cobs):
                    d = math.dist(self.nodes[i], self.nodes[j])
                    self.adj[i][j] = d
                    self.adj[j][i] = d
        self.build_time_s = time.perf_counter() - t0
        return self

    def _neighbours(self, p: Point, exclude: int = -1) -> List[int]:
        cand = [(math.dist(p, q), j) for j, q in enumerate(self.nodes)
                if j != exclude and j in self.adj]
        cand = [c for c in cand if c[0] <= self.max_edge]
        return [j for _, j in heapq.nsmallest(self.k, cand)]

    @property
    def n_edges(self) -> int:
        return sum(len(v) for v in self.adj.values()) // 2

    # ---- query phase
    def _connect(self, p: Point) -> List[Tuple[int, float]]:
        return [(j, math.dist(p, self.nodes[j])) for j in self._neighbours(p)
                if edge_free(p, self.nodes[j], self.cobs)]

    def query(self, start: Point, goal: Point, smooth: bool = True) -> Optional[List[Point]]:
        start, goal = tuple(start), tuple(goal)
        if not (point_free(start, self.cobs, self.bounds) and point_free(goal, self.cobs, self.bounds)):
            return None
        if edge_free(start, goal, self.cobs):
            return [start, goal]
        s_links, g_links = self._connect(start), self._connect(goal)
        if not s_links or not g_links:
            return None
        goal_set = {j: d for j, d in g_links}
        # A* over roadmap nodes; virtual start node -1, virtual goal node -2
        h = lambda j: math.dist(self.nodes[j], goal)  # noqa: E731
        g_cost = {j: d for j, d in s_links}
        parent: Dict[int, int] = {j: -1 for j, _ in s_links}
        openq = [(d + h(j), j) for j, d in s_links]
        heapq.heapify(openq)
        best_goal, best_cost, closed = None, math.inf, set()
        while openq:
            f, j = heapq.heappop(openq)
            if f >= best_cost:
                break
            if j in closed:
                continue
            closed.add(j)
            if j in goal_set and g_cost[j] + goal_set[j] < best_cost:
                best_goal, best_cost = j, g_cost[j] + goal_set[j]
            for n, w in self.adj[j].items():
                c = g_cost[j] + w
                if c < g_cost.get(n, math.inf):
                    g_cost[n], parent[n] = c, j
                    heapq.heappush(openq, (c + h(n), n))
        if best_goal is None:
            return None
        path, j = [goal], best_goal
        while j != -1:
            path.append(self.nodes[j])
            j = parent[j]
        path.append(start)
        path.reverse()
        return self.shortcut(path) if smooth else path

    def shortcut(self, path: List[Point]) -> List[Point]:
        """Greedy shortcut smoothing: from each waypoint jump to the farthest
        later waypoint that is directly visible."""
        out, i = [path[0]], 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1 and not edge_free(path[i], path[j], self.cobs):
                j -= 1
            out.append(path[j])
            i = j
        return out

    # ---- dynamic change: blocked corridor (re-planning support)
    def add_obstacle(self, rect: Rect) -> Tuple[int, int]:
        """Add an obstacle (e.g. a bed blocking a corridor) and remove the nodes
        and edges it invalidates, without rebuilding the roadmap.
        Returns (nodes_removed, edges_removed)."""
        self.obstacles.append(rect)
        box = inflate([rect], self.r)[0]
        self.cobs.append(box)
        bad_nodes = [i for i in self.adj if not point_free(self.nodes[i], [box], self.bounds)]
        edges_removed = 0
        for i in bad_nodes:
            for j in list(self.adj[i]):
                del self.adj[j][i]
                edges_removed += 1
            del self.adj[i]
        for i in self.adj:
            for j in [j for j in self.adj[i] if j > i and segment_hits_box(self.nodes[i], self.nodes[j], box)]:
                del self.adj[i][j]
                del self.adj[j][i]
                edges_removed += 1
        return len(bad_nodes), edges_removed


# --------------------------------------------------------------- module API
_ROADMAP: Optional[PRM] = None
_LOCK = threading.RLock()     # the client plans in one thread and blocks from another


def get_roadmap() -> PRM:
    """Shared roadmap, built once on first use and reused for every order."""
    global _ROADMAP
    with _LOCK:
        if _ROADMAP is None:
            _ROADMAP = PRM().build()
        return _ROADMAP


def plan(start: Point, goal: Point) -> Optional[List[Point]]:
    """Interface for the client: collision-free waypoints start -> goal, or None."""
    with _LOCK:
        return get_roadmap().query(start, goal)


def block(rect: Rect) -> Tuple[int, int]:
    """Mark an area as blocked in the shared roadmap (see PRM.add_obstacle)."""
    with _LOCK:
        return get_roadmap().add_obstacle(rect)

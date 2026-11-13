"""Sanity tests for baseline planners (RRT & Grid A*).

Run: python3 -m baseline.test_baseline

Author: Divyanshu Dhyani (M2)
Module: baseline/
"""

import itertools
import math

from client import config
from planner import hospital_map as hm
from planner.prm import edge_free, point_free
from baseline.grid_astar import GridAStar
from baseline.rrt import RRT

L = config.LOCATIONS


def test_rrt_single_query():
    rrt = RRT(step_size=0.4, goal_bias=0.2, max_iter=3000, seed=123)
    start = L["pharmacy"]
    goal = L["ward1"]
    path = rrt.query(start, goal)
    assert path is not None, "RRT failed to find path from pharmacy to ward1"
    assert path[0] == start and path[-1] == goal
    assert all(edge_free(u, v, rrt.cobs) for u, v in zip(path, path[1:])), "RRT path collided with obstacles!"


def test_grid_astar_single_query():
    astar = GridAStar(resolution=0.20)
    start = L["pharmacy"]
    goal = L["ward1"]
    path = astar.query(start, goal)
    assert path is not None, "Grid A* failed to find path from pharmacy to ward1"
    assert path[0] == start and path[-1] == goal
    assert all(edge_free(u, v, astar.cobs) for u, v in zip(path, path[1:])), "Grid A* path collided with obstacles!"


def test_rrt_corridor_navigation():
    # Reception to ICU
    rrt = RRT(step_size=0.4, goal_bias=0.2, max_iter=3000, seed=42)
    start = L["reception"]
    goal = L["icu"]
    path = rrt.query(start, goal)
    assert path is not None, "RRT failed to find path from reception to icu"
    assert all(edge_free(u, v, rrt.cobs) for u, v in zip(path, path[1:]))


def test_grid_astar_all_wards():
    astar = GridAStar(resolution=0.20)
    for ward in ["ward1", "ward2", "ward3", "icu"]:
        path = astar.query(L["pharmacy"], L[ward])
        assert path is not None, f"Grid A* failed pharmacy -> {ward}"
        assert all(edge_free(u, v, astar.cobs) for u, v in zip(path, path[1:]))


if __name__ == "__main__":
    test_rrt_single_query()
    print("PASS test_rrt_single_query")
    test_grid_astar_single_query()
    print("PASS test_grid_astar_single_query")
    test_rrt_corridor_navigation()
    print("PASS test_rrt_corridor_navigation")
    test_grid_astar_all_wards()
    print("PASS test_grid_astar_all_wards")
    print("\nALL BASELINE TESTS PASSED SUCCESSFULLY!")


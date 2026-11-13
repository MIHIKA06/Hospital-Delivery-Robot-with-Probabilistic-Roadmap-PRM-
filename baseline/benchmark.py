"""Comprehensive benchmarking harness for Hospital Delivery Robot path planners.

Compares:
1. PRM (Door-seeded - Proposed Novelty)
2. PRM (Bridge test - Hsu et al.)
3. PRM (Uniform - Classical Kavraki et al.)
4. PRM (Door-seeded, N=100 - Low-sample efficiency)
5. RRT (Rapidly-exploring Random Tree - LaValle single-query baseline)
6. Grid A* (Deterministic discrete-search baseline)

Across all 72 ordered pairs of clinical hospital locations.
Logs: Planning Time, Path Length, Waypoint Count, and Success Rate.

Author: Divyanshu Dhyani (M2)
Module: baseline/
"""

from __future__ import annotations

import csv
import itertools
import math
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from baseline.grid_astar import GridAStar
from baseline.rrt import RRT
from client import config
from planner import hospital_map as hm
from planner.prm import PRM, edge_free, inflate

Point = Tuple[float, float]


def compute_path_length(path: Optional[List[Point]]) -> float:
    if not path or len(path) < 2:
        return 0.0
    return sum(math.dist(a, b) for a, b in zip(path, path[1:]))


def run_benchmark():
    locations = config.LOCATIONS
    pairs = list(itertools.permutations(locations.keys(), 2))  # 72 pairs
    total_pairs = len(pairs)

    print(f"================================================================================")
    print(f"  HOSPITAL DELIVERY ROBOT: PATH PLANNING BENCHMARK HARNESS")
    print(f"  Author: Divyanshu Dhyani (M2 - SAP ID: 500122522)")
    print(f"  Evaluating {total_pairs} location pairs across 6 planner configurations")
    print(f"================================================================================\n")

    os.makedirs("results", exist_ok=True)
    detailed_csv_path = "results/benchmark_detailed.csv"
    summary_csv_path = "results/benchmark_summary.csv"

    detailed_records: List[Dict[str, Any]] = []
    summary_records: List[Dict[str, Any]] = []

    # 1. Define Planner Configurations
    planner_configs = [
        {
            "name": "PRM (Door-seeded, N=300)",
            "type": "multi-query",
            "builder": lambda: PRM(n_samples=300, k=10, sampler="door", seed=42).build(),
        },
        {
            "name": "PRM (Bridge, N=300)",
            "type": "multi-query",
            "builder": lambda: PRM(n_samples=300, k=10, sampler="bridge", seed=42).build(),
        },
        {
            "name": "PRM (Uniform, N=300)",
            "type": "multi-query",
            "builder": lambda: PRM(n_samples=300, k=10, sampler="uniform", seed=42).build(),
        },
        {
            "name": "PRM (Door-seeded, N=100)",
            "type": "multi-query",
            "builder": lambda: PRM(n_samples=100, k=10, sampler="door", seed=42).build(),
        },
        {
            "name": "RRT Baseline (Single-Query)",
            "type": "single-query",
            "runner": lambda s, g: RRT(step_size=0.40, goal_bias=0.20, max_iter=3500, seed=42).query(s, g),
            "build_time_s": 0.0,
        },
        {
            "name": "Grid A* Baseline (res=0.20m)",
            "type": "discrete-grid",
            "builder": lambda: GridAStar(resolution=0.20),
        },
    ]

    for p_cfg in planner_configs:
        name = p_cfg["name"]
        p_type = p_cfg["type"]
        print(f"Evaluating [{name}]...")

        build_time_ms = 0.0
        query_fn: Callable[[Point, Point], Optional[List[Point]]]

        if p_type == "multi-query":
            t0 = time.perf_counter()
            roadmap: PRM = p_cfg["builder"]()
            build_time_ms = (time.perf_counter() - t0) * 1000.0
            query_fn = lambda s, g: roadmap.query(s, g)
        elif p_type == "discrete-grid":
            t0 = time.perf_counter()
            grid_planner: GridAStar = p_cfg["builder"]()
            build_time_ms = (time.perf_counter() - t0) * 1000.0
            query_fn = lambda s, g: grid_planner.query(s, g)
        else:  # single-query RRT
            build_time_ms = 0.0
            query_fn = p_cfg["runner"]

        success_count = 0
        query_times_ms: List[float] = []
        path_lengths_m: List[float] = []
        waypoint_counts: List[int] = []

        for src_name, dst_name in pairs:
            start_pt = locations[src_name]
            goal_pt = locations[dst_name]

            q_t0 = time.perf_counter()
            path = query_fn(start_pt, goal_pt)
            q_time_ms = (time.perf_counter() - q_t0) * 1000.0

            valid = False
            p_len = 0.0
            n_wp = 0

            if path is not None and len(path) >= 2:
                # Verify collision freedom
                cobs = inflate(hm.OBSTACLES, hm.ROBOT_RADIUS)
                if all(edge_free(u, v, cobs) for u, v in zip(path, path[1:])):
                    valid = True
                    p_len = compute_path_length(path)
                    n_wp = len(path)

            if valid:
                success_count += 1
                query_times_ms.append(q_time_ms)
                path_lengths_m.append(p_len)
                waypoint_counts.append(n_wp)

            detailed_records.append({
                "planner": name,
                "start": src_name,
                "goal": dst_name,
                "success": valid,
                "query_time_ms": round(q_time_ms, 3),
                "path_length_m": round(p_len, 3) if valid else None,
                "waypoints": n_wp if valid else None,
            })

        success_rate = (success_count / total_pairs) * 100.0
        mean_query_time = sum(query_times_ms) / len(query_times_ms) if query_times_ms else 0.0
        median_query_time = sorted(query_times_ms)[len(query_times_ms) // 2] if query_times_ms else 0.0
        max_query_time = max(query_times_ms) if query_times_ms else 0.0
        mean_path_len = sum(path_lengths_m) / len(path_lengths_m) if path_lengths_m else 0.0
        mean_waypoints = sum(waypoint_counts) / len(waypoint_counts) if waypoint_counts else 0.0

        summary_records.append({
            "planner": name,
            "type": p_type,
            "success_rate_pct": round(success_rate, 1),
            "successful_queries": f"{success_count}/{total_pairs}",
            "build_time_ms": round(build_time_ms, 2),
            "mean_query_time_ms": round(mean_query_time, 3),
            "median_query_time_ms": round(median_query_time, 3),
            "max_query_time_ms": round(max_query_time, 3),
            "mean_path_length_m": round(mean_path_len, 3),
            "mean_waypoints": round(mean_waypoints, 1),
        })

    # Save Detailed CSV
    with open(detailed_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["planner", "start", "goal", "success", "query_time_ms", "path_length_m", "waypoints"]
        )
        writer.writeheader()
        writer.writerows(detailed_records)

    # Save Summary CSV
    with open(summary_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "planner", "type", "success_rate_pct", "successful_queries",
                "build_time_ms", "mean_query_time_ms", "median_query_time_ms",
                "max_query_time_ms", "mean_path_length_m", "mean_waypoints"
            ]
        )
        writer.writeheader()
        writer.writerows(summary_records)

    # Print Formatted Report Table
    print("\n" + "=" * 105)
    print(f"{'BENCHMARK SUMMARY RESULTS TABLE (Group G06 - Divyanshu M2)':^105}")
    print("=" * 105)
    header = (
        f"{'Planner':<30} | {'Success':<8} | {'Build (ms)':<10} | "
        f"{'Mean Q (ms)':<11} | {'Max Q (ms)':<10} | {'Path (m)':<8} | {'Waypoints':<9}"
    )
    print(header)
    print("-" * 105)

    for r in summary_records:
        row = (
            f"{r['planner']:<30} | "
            f"{r['success_rate_pct']:>6.1f}% | "
            f"{r['build_time_ms']:>10.1f} | "
            f"{r['mean_query_time_ms']:>11.3f} | "
            f"{r['max_query_time_ms']:>10.2f} | "
            f"{r['mean_path_length_m']:>8.2f} | "
            f"{r['mean_waypoints']:>9.1f}"
        )
        print(row)
    print("=" * 105)
    print(f"\nSaved detailed log to: {detailed_csv_path}")
    print(f"Saved summary table to: {summary_csv_path}\n")


if __name__ == "__main__":
    run_benchmark()

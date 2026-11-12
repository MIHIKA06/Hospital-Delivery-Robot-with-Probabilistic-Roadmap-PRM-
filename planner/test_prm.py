"""Sanity tests for the PRM planner.  Run:  python3 -m planner.test_prm"""

import itertools
import math

from client import config
from . import hospital_map as hm
from .prm import PRM, edge_free, point_free, segment_hits_box

L = config.LOCATIONS


def test_segment_box():
    box = (0, 0, 1, 1)
    assert segment_hits_box((-1, 0.5), (2, 0.5), box)        # straight through
    assert not segment_hits_box((-1, 2), (2, 2), box)        # passes above
    assert not segment_hits_box((-1, -1), (-0.5, 3), box)    # passes left


def test_locations_free():
    p = PRM()
    for name, xy in L.items():
        assert point_free(xy, p.cobs, p.bounds), f"{name} is inside an obstacle"


def test_all_pairs_door_sampler():
    for seed in range(1, 6):
        p = PRM(n_samples=200, seed=seed).build()
        for a, b in itertools.permutations(L, 2):
            path = p.query(L[a], L[b])
            assert path, f"seed {seed}: no path {a} -> {b}"
            assert path[0] == L[a] and path[-1] == L[b]
            assert all(edge_free(u, v, p.cobs) for u, v in zip(path, path[1:]))


def test_blocked_corridor_replans():
    p = PRM().build()
    blocker = (-1.9, -0.4, 0.6, 0.4)
    before = p.query(L["lab"], L["ward1"])
    p.add_obstacle(blocker)
    after = p.query(L["lab"], L["ward1"])
    assert after and all(edge_free(u, v, p.cobs) for u, v in zip(after, after[1:]))
    length = lambda q: sum(math.dist(u, v) for u, v in zip(q, q[1:]))  # noqa: E731
    assert length(after) >= length(before) - 1e-9


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)

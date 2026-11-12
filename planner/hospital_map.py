"""2-D floor plan of the hospital used by the planner.

All obstacles are axis-aligned rectangles (xmin, ymin, xmax, ymax) in metres,
in the same world frame as CoppeliaSim and client/config.py. The CoppeliaSim
hospital scene (scene/hospital.ttt) must be built from THIS map so that the
planner and the simulator agree.

Layout (12 m x 12 m):

      x=-6          x=-2         x=2           x=6
 y=6  +-------------+------------+-------------+
      |  PHARMACY   |            |   WARD 1    |
      |            door  CORRIDOR door          |
 y=0  +-------------+  (reception,+-------------+  y=2.75
      |    LAB      |  emergency,|   WARD 2    |  y=0
      |            door  home)  door  WARD 3   |  y=-2.75
      |             |            |    ICU      |
 y=-6 +-------------+------------+-------------+

Doors are 1.0 m wide; with a 0.30 m robot radius the free gap is only 0.4 m,
which makes the doorways the "narrow passages" of the PRM problem.
"""

from __future__ import annotations

from typing import List, Tuple

Rect = Tuple[float, float, float, float]

BOUNDS: Rect = (-6.0, -6.0, 6.0, 6.0)
ROBOT_RADIUS = 0.30          # Pioneer P3-DX footprint radius plus small margin
WALL = 0.10                  # wall thickness


def _vwall(x: float, y0: float, y1: float) -> Rect:
    return (x - WALL / 2, y0, x + WALL / 2, y1)


def _hwall(y: float, x0: float, x1: float) -> Rect:
    return (x0, y - WALL / 2, x1, y + WALL / 2)


WALLS: List[Rect] = [
    # outer walls
    _hwall(-6.0, -6.0, 6.0), _hwall(6.0, -6.0, 6.0),
    _vwall(-6.0, -6.0, 6.0), _vwall(6.0, -6.0, 6.0),
    # left block: pharmacy (top) / lab (bottom); doors at y=3 and y=-3
    _vwall(-2.0, -6.0, -3.5), _vwall(-2.0, -2.5, 2.5), _vwall(-2.0, 3.5, 6.0),
    _hwall(0.0, -6.0, -2.0),
    # right block: ward1, ward2, ward3, icu; doors at y=4, 1.5, -1.5, -4
    _vwall(2.0, -6.0, -4.5), _vwall(2.0, -3.5, -2.0), _vwall(2.0, -1.0, 1.0),
    _vwall(2.0, 2.0, 3.5), _vwall(2.0, 4.5, 6.0),
    _hwall(2.75, 2.0, 6.0), _hwall(0.0, 2.0, 6.0), _hwall(-2.75, 2.0, 6.0),
]

FURNITURE: List[Rect] = [
    (-5.8, 4.6, -4.6, 5.8),     # pharmacy shelves
    (-5.8, 1.0, -5.2, 2.4),     # pharmacy fridge
    (-5.8, -5.8, -4.4, -5.0),   # lab bench
    (4.8, 4.6, 5.8, 5.8),       # ward 1 bed
    (4.8, 0.3, 5.8, 1.1),       # ward 2 bed
    (4.8, -2.4, 5.8, -1.8),     # ward 3 bed
    (4.6, -5.8, 5.8, -4.8),     # ICU bed
    (-1.0, -5.9, 1.0, -5.0),    # reception desk
    (0.9, 2.2, 1.5, 3.0),       # parked trolley in corridor
    (-1.6, -1.6, -1.0, -0.6),   # bench in corridor
]

OBSTACLES: List[Rect] = WALLS + FURNITURE

# Door centres and the axis the robot crosses them along ("x" = door in a
# vertical wall, robot moves in x). Used by the door-seeded PRM sampler.
DOORS: List[Tuple[float, float, str]] = [
    (-2.0, 3.0, "x"), (-2.0, -3.0, "x"),                      # pharmacy, lab
    (2.0, 4.0, "x"), (2.0, 1.5, "x"), (2.0, -1.5, "x"), (2.0, -4.0, "x"),  # wards, ICU
]

"""Path-following controller for the Pioneer P3-DX in CoppeliaSim (Sumit's module).

Interface used by the client (client/interfaces.py):
    follow(sim, robot_handle, path, should_stop) -> bool

How it works
------------
The PRM path is a list of waypoints joined by straight segments. The robot
follows them one segment at a time:

1. Carrot on the current segment. Project the robot onto the segment and aim
   at a point LOOKAHEAD metres further along it. The carrot never leaves the
   current segment, so the robot does not cut corners. That matters in the
   1.0 m doorways, where the PRM leaves only about 0.4 m of clearance.
2. PID on the heading error to the carrot gives the turn rate w.
3. The forward speed v drops as the heading error grows. Above TURN_IN_PLACE
   the robot stops and rotates on the spot, for example at a sharp corner
   after a waypoint.
4. Differential drive: (v, w) are turned into left and right wheel speeds with
   the measured P3-DX geometry (wheel radius 0.0975 m, track 0.331 m).

The controller runs in stepping mode, one control update per 50 ms
simulation step, so it behaves the same however fast the simulator runs.
With REALTIME = True it also sleeps so that the motion plays back at real
speed in the GUI.

It returns False on an emergency stop (`should_stop()`), when the robot
stops making progress (STUCK_TIMEOUT), or when it leaves the path by more
than MAX_CROSS_TRACK. On every exit it stops the wheels.
"""

from __future__ import annotations

import math
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple

Point = Tuple[float, float]

# ---- robot geometry (measured from the CoppeliaSim Pioneer P3-DX model) ----
WHEEL_RADIUS = 0.0975        # m
TRACK = 0.331                # m, distance between the two wheels
MAX_WHEEL_SPEED = 2 * math.pi  # rad/s, about 0.61 m/s at the rim

# ---- controller tuning ----
V_MAX = 0.45                 # m/s cruise speed
V_MIN = 0.08                 # m/s creep speed near the goal
W_MAX = 1.6                  # rad/s
LOOKAHEAD = 0.35             # m, carrot distance along the current segment
KP, KI, KD = 2.2, 0.05, 0.25  # heading PID
TURN_IN_PLACE = math.radians(50)  # larger heading error: stop and rotate
SLOW_RADIUS = 0.6            # m, start slowing down this close to the goal
GOAL_TOL = 0.10              # m, arrival tolerance at the final waypoint
SWITCH_TOL = 0.15            # m, move to the next segment this close to its end
STUCK_TIMEOUT = 8.0          # s of sim time with no progress, then give up
MAX_CROSS_TRACK = 0.8        # m off the path, then give up (collision or slip)
REALTIME = True              # sleep so the GUI shows real-time motion

# Last run statistics, for the experiments (Prachi): RMS cross-track error, etc.
last_stats: Dict[str, float] = {}


def wrap(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


def project(p: Point, a: Point, b: Point) -> Tuple[float, float, float]:
    """Return (t, along, cross) of p relative to segment a-b.
    t is in [0, 1], `along` is metres from a, `cross` is the signed lateral
    error (positive = left of the segment)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return 1.0, 0.0, math.dist(p, a)
    ux, uy = dx / L, dy / L
    px, py = p[0] - a[0], p[1] - a[1]
    along = px * ux + py * uy
    cross = ux * py - uy * px
    return max(0.0, min(1.0, along / L)), along, cross


def unicycle_to_wheels(v: float, w: float) -> Tuple[float, float]:
    """Body velocity (v, w) -> (left, right) wheel speeds in rad/s, scaled
    together if either would exceed MAX_WHEEL_SPEED (keeps the curvature)."""
    wl = (v - w * TRACK / 2) / WHEEL_RADIUS
    wr = (v + w * TRACK / 2) / WHEEL_RADIUS
    s = max(abs(wl), abs(wr)) / MAX_WHEEL_SPEED
    if s > 1:
        wl, wr = wl / s, wr / s
    return wl, wr


class HeadingPID:
    def __init__(self, kp=KP, ki=KI, kd=KD, i_max=0.5):
        self.kp, self.ki, self.kd, self.i_max = kp, ki, kd, i_max
        self.i = 0.0
        self.prev: Optional[float] = None

    def reset(self):
        self.i, self.prev = 0.0, None

    def __call__(self, err: float, dt: float) -> float:
        self.i = max(-self.i_max, min(self.i_max, self.i + err * dt))
        d = 0.0 if self.prev is None else wrap(err - self.prev) / dt
        self.prev = err
        return self.kp * err + self.ki * self.i + self.kd * d


def control_step(pose: Tuple[float, float, float], path: Sequence[Point], seg: int,
                 pid: HeadingPID, dt: float) -> Tuple[float, float, int, bool, float]:
    """One controller update. Pure function of the pose, so it can be unit
    tested without CoppeliaSim.

    Returns (v, w, seg, arrived, cross_track_error)."""
    x, y, yaw = pose
    p = (x, y)
    last = len(path) - 2
    # move on to the next segment once we are near the end of this one
    while seg < last:
        t, _, _ = project(p, path[seg], path[seg + 1])
        if t >= 1.0 or math.dist(p, path[seg + 1]) < SWITCH_TOL:
            seg += 1
            pid.reset()
        else:
            break
    a, b = path[seg], path[seg + 1]
    goal = path[-1]
    d_goal = math.dist(p, goal)
    _, along, cross = project(p, a, b)
    if seg == last and d_goal < GOAL_TOL:
        return 0.0, 0.0, seg, True, cross

    L = math.dist(a, b)
    s = min(L, max(0.0, along) + LOOKAHEAD)
    carrot = (a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L) if L > 1e-9 else b
    if math.dist(p, carrot) < 0.05:
        carrot = b
    err = wrap(math.atan2(carrot[1] - y, carrot[0] - x) - yaw)

    w = max(-W_MAX, min(W_MAX, pid(err, dt)))
    if abs(err) > TURN_IN_PLACE:
        v = 0.0                                   # rotate on the spot
    else:
        v = V_MAX * math.cos(err) ** 2            # slow down when misaligned
        # slow down for the goal, and for the corner at the end of this segment
        d_corner = math.dist(p, b) if seg < last else d_goal
        v = min(v, max(V_MIN, V_MAX * d_corner / SLOW_RADIUS)) if d_corner < SLOW_RADIUS else v
        if seg == last:
            v = min(v, max(V_MIN, 0.8 * d_goal))
    return v, w, seg, False, cross


# ------------------------------------------------------------ CoppeliaSim side
def _motors(sim, robot_handle) -> Tuple[int, int]:
    alias = sim.getObjectAlias(robot_handle, 1)        # e.g. "/PioneerP3DX"
    return sim.getObject(alias + "/leftMotor"), sim.getObject(alias + "/rightMotor")


def _set_stepping(sim, on: bool) -> bool:
    """Turn stepping mode on/off. Returns the previous state (best effort)."""
    try:
        return bool(sim.setStepping(on))
    except Exception:
        return False


def _pose(sim, robot) -> Tuple[float, float, float]:
    x, y, _ = sim.getObjectPosition(robot, sim.handle_world)
    yaw = sim.getObjectOrientation(robot, sim.handle_world)[2]
    return x, y, yaw


def follow(sim, robot_handle, path: Sequence[Point],
           should_stop: Callable[[], bool] = lambda: False) -> bool:
    """Drive the robot along `path` (list of (x, y)). True on arrival."""
    path = [tuple(map(float, q)) for q in path]
    # drop repeated points
    path = [q for i, q in enumerate(path) if i == 0 or math.dist(q, path[i - 1]) > 1e-6]
    last_stats.clear()
    if len(path) < 2:
        return True

    left, right = _motors(sim, robot_handle)
    if sim.getSimulationState() == sim.simulation_stopped:
        sim.startSimulation()
    was_stepping = _set_stepping(sim, True)
    dt = sim.getSimulationTimeStep()
    pid = HeadingPID()
    seg = 0
    best_remaining = math.inf
    last_progress_t = sim.getSimulationTime()
    t_start = last_progress_t
    sq_cross, n, max_cross = 0.0, 0, 0.0
    ok = False
    try:
        while True:
            if should_stop():
                return False
            pose = _pose(sim, robot_handle)
            v, w, seg, arrived, cross = control_step(pose, path, seg, pid, dt)
            sq_cross += cross * cross
            n += 1
            max_cross = max(max_cross, abs(cross))
            if arrived:
                ok = True
                return True
            if abs(cross) > MAX_CROSS_TRACK:
                print(f"[controller] left the path by {cross:.2f} m, aborting")
                return False

            # progress = remaining path length; watchdog against getting stuck
            _, along, _ = project(pose[:2], path[seg], path[seg + 1])
            remaining = (math.dist(path[seg], path[seg + 1]) - along
                         + sum(math.dist(a, b) for a, b in zip(path[seg + 1:], path[seg + 2:])))
            now = sim.getSimulationTime()
            if remaining < best_remaining - 0.02:
                best_remaining, last_progress_t = remaining, now
            elif now - last_progress_t > STUCK_TIMEOUT:
                print(f"[controller] no progress for {STUCK_TIMEOUT:.0f} s, robot is stuck")
                return False

            wl, wr = unicycle_to_wheels(v, w)
            sim.setJointTargetVelocity(left, wl)
            sim.setJointTargetVelocity(right, wr)
            t0 = time.perf_counter()
            sim.step()
            if REALTIME:
                time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
    finally:
        sim.setJointTargetVelocity(left, 0.0)
        sim.setJointTargetVelocity(right, 0.0)
        try:
            sim.step()              # apply the zero command
        except Exception:
            pass
        _set_stepping(sim, was_stepping)
        if n:
            x, y, _ = _pose(sim, robot_handle)
            last_stats.update({
                "arrived": float(ok),
                "sim_time_s": sim.getSimulationTime() - t_start,
                "rms_cross_track_m": math.sqrt(sq_cross / n),
                "max_cross_track_m": max_cross,
                "final_error_m": math.dist((x, y), path[-1]),
            })

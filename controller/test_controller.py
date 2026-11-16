"""Offline test of the controller with an ideal differential-drive model
(no CoppeliaSim needed):  python3 -m controller.test_controller"""
import math

from client import config
from planner.prm import plan

from . import controller as ctl


def simulate(path, pose=None, dt=0.05, t_max=120.0):
    x, y = path[0]
    yaw = 0.0 if pose is None else pose
    pid, seg, t, worst = ctl.HeadingPID(), 0, 0.0, 0.0
    while t < t_max:
        v, w, seg, arrived, cross = ctl.control_step((x, y, yaw), path, seg, pid, dt)
        worst = max(worst, abs(cross))
        if arrived:
            return True, t, worst
        wl, wr = ctl.unicycle_to_wheels(v, w)          # respect wheel limits
        v = (wl + wr) * ctl.WHEEL_RADIUS / 2
        w = (wr - wl) * ctl.WHEEL_RADIUS / ctl.TRACK
        x += v * math.cos(yaw) * dt
        y += v * math.sin(yaw) * dt
        yaw = ctl.wrap(yaw + w * dt)
        t += dt
    return False, t, worst


def main():
    names = list(config.LOCATIONS)
    n = 0
    for a in names:
        for b in names:
            if a == b:
                continue
            p = plan(config.LOCATIONS[a], config.LOCATIONS[b])
            assert p, (a, b)
            ok, t, worst = simulate(p)
            assert ok, f"{a}->{b} did not arrive"
            assert worst < 0.25, f"{a}->{b} cross-track {worst:.2f} m"
            n += 1
    assert ctl.unicycle_to_wheels(0.0, 0.0) == (0.0, 0.0)
    wl, wr = ctl.unicycle_to_wheels(10.0, 0.0)
    assert abs(wl - ctl.MAX_WHEEL_SPEED) < 1e-9 and wl == wr
    print(f"controller OK: {n} routes followed, all arrived")


if __name__ == "__main__":
    main()

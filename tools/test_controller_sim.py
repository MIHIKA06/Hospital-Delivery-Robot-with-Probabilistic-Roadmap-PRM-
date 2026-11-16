"""Drive the robot through a set of PRM routes in CoppeliaSim and report
tracking error per route (controller test; CoppeliaSim running with
scene/hospital.ttt open).

    python3 tools/test_controller_sim.py [--fast]
"""
import argparse, math, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from client import config
from controller import controller as ctl
from planner.prm import plan
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

ap = argparse.ArgumentParser()
ap.add_argument("--fast", action="store_true", help="do not slow down to real time")
ap.add_argument("--route", nargs="*", default=["pharmacy", "ward1", "lab", "icu", "emergency", "ward3", "reception", "ward2", "home"])
a = ap.parse_args()
ctl.REALTIME = not a.fast

sim = RemoteAPIClient().require("sim")
robot = sim.getObject(config.ROBOT_PATH)
locs = dict(config.LOCATIONS)
for n in locs:
    h = sim.getObject(f"/loc_{n}"); locs[n] = tuple(sim.getObjectPosition(h, sim.handle_world)[:2])
sim.startSimulation()
print(f"{'leg':24s} {'ok':>3s} {'path m':>7s} {'sim s':>6s} {'rms xte':>8s} {'max xte':>8s} {'end err':>8s}")
fails = 0
for goal in a.route:
    x, y, _ = sim.getObjectPosition(robot, sim.handle_world)
    p = plan((x, y), locs[goal])
    if not p:
        print("no path to", goal); fails += 1; continue
    L = sum(math.dist(u, v) for u, v in zip(p, p[1:]))
    ok = ctl.follow(sim, robot, p, lambda: False)
    s = ctl.last_stats
    fails += not ok
    print(f"-> {goal:21s} {'yes' if ok else 'NO':>3s} {L:7.2f} {s['sim_time_s']:6.1f} "
          f"{s['rms_cross_track_m']:8.3f} {s['max_cross_track_m']:8.3f} {s['final_error_m']:8.3f}")
sim.stopSimulation()
print("all legs reached" if not fails else f"{fails} leg(s) failed")

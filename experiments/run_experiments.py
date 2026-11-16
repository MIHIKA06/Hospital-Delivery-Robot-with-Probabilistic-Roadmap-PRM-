"""All offline experiments for the report. Writes results/E*.json.

    python3 -m experiments.run_experiments          # about 2-4 minutes

E1  PRM sampler comparison (uniform / bridge / door) vs number of samples
E2  PRM vs RRT: success, planning time, path length, total time for many orders
E3  Order dispatch: priority vs first-come-first-served waiting times
E4  Path-following controller: cross-track error, ideal and with noise/slip
E5  Blocked corridor: local roadmap repair vs full rebuild
(E6 = CoppeliaSim tour and emergency stop, run by tools/test_controller_sim.py
 and the client; numbers recorded in results/E6_coppeliasim.json.)
"""

from __future__ import annotations

import itertools
import json
import math
import os
import random
import statistics as st
import time

from baseline.rrt import RRT
from client import config
from controller import controller as ctl
from planner import hospital_map as hm
from planner.prm import PRM, edge_free

L = config.LOCATIONS
PAIRS = list(itertools.permutations(L, 2))
OUT = "results"


def plen(p):
    return sum(math.dist(u, v) for u, v in zip(p, p[1:]))


def save(name, data):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(data, f, indent=1)
    print("saved", name)


# ------------------------------------------------------------------ E1
def e1(seeds=range(1, 11)):
    rows = []
    for sampler in ("uniform", "bridge", "door"):
        for n in (50, 100, 200, 300, 500):
            succ, full, build, edges = [], 0, [], []
            for s in seeds:
                p = PRM(n_samples=n, sampler=sampler, seed=s).build()
                ok = sum(p.query(L[a], L[b]) is not None for a, b in PAIRS) / len(PAIRS)
                succ.append(ok)
                full += ok == 1.0
                build.append(p.build_time_s * 1000)
                edges.append(p.n_edges)
            rows.append(dict(sampler=sampler, n=n, success_pct=100 * st.mean(succ),
                             full_seeds=full, n_seeds=len(seeds),
                             build_ms=st.mean(build), edges=st.mean(edges)))
            print(f"E1 {sampler:7s} n={n:3d} success {rows[-1]['success_pct']:5.1f}%  full {full}/10")
    save("E1_samplers.json", rows)


# ------------------------------------------------------------------ E2
def e2(seeds=range(1, 6)):
    res = {}
    for name in ("PRM (door, n=300)", "RRT"):
        succ, qms, lens, total = [], [], [], []
        for s in seeds:
            t0 = time.perf_counter()
            if name.startswith("PRM"):
                planner = PRM(seed=s).build()
            else:
                planner = RRT(seed=s)
            for a, b in PAIRS:
                t = time.perf_counter()
                path = planner.query(L[a], L[b])
                qms.append((time.perf_counter() - t) * 1000)
                succ.append(path is not None)
                if path:
                    lens.append(plen(path))
            total.append((time.perf_counter() - t0) * 1000)
        res[name] = dict(success_pct=100 * sum(succ) / len(succ), query_ms_mean=st.mean(qms),
                         query_ms_max=max(qms), path_len_mean=st.mean(lens),
                         total_ms_72_orders=st.mean(total))
        print("E2", name, {k: round(v, 2) for k, v in res[name].items()})
    # cumulative time vs number of orders (one seed)
    prm = PRM(seed=1)
    t0 = time.perf_counter()
    prm.build()
    build_ms = (time.perf_counter() - t0) * 1000
    rrt = RRT(seed=1)
    rng = random.Random(7)
    orders = [rng.sample(list(L), 2) for _ in range(200)]
    cum_prm, cum_rrt, cp, cr = [], [], build_ms, 0.0
    for a, b in orders:
        t = time.perf_counter(); prm.query(L[a], L[b]); cp += (time.perf_counter() - t) * 1000
        t = time.perf_counter(); rrt.query(L[a], L[b]); cr += (time.perf_counter() - t) * 1000
        cum_prm.append(cp)
        cum_rrt.append(cr)
    res["cumulative"] = dict(prm_build_ms=build_ms, prm=cum_prm, rrt=cum_rrt)
    save("E2_prm_vs_rrt.json", res)


# ------------------------------------------------------------------ E3
def e3(trials=30, n_orders=40, urgent_frac=0.25, speed=0.35, handling_s=20.0):
    """Discrete-event simulation of one robot serving random orders. Travel time
    = PRM path length / mean speed; handling_s = loading + unloading time."""
    prm = PRM(seed=1).build()
    dist = {(a, b): plen(prm.query(L[a], L[b])) for a, b in PAIRS}
    dist.update({(a, a): 0.0 for a in L})
    out = {}
    for load_name, mean_gap in (("low", 120.0), ("medium", 75.0), ("high", 55.0)):
        res = {"fifo": {"urgent": [], "normal": []}, "priority": {"urgent": [], "normal": []}}
        for tr in range(trials):
            rng = random.Random(100 + tr)
            t, orders = 0.0, []
            stations = [k for k in L if k != "home"]
            for i in range(n_orders):
                t += rng.expovariate(1 / mean_gap)
                a, b = rng.sample(stations, 2)
                orders.append((t, i, rng.random() < urgent_frac, a, b))
            for policy in ("fifo", "priority"):
                clock, pos, waiting, k = 0.0, "home", [], 0
                pending = list(orders)
                done = 0
                while done < n_orders:
                    while k < n_orders and pending[k][0] <= clock:
                        waiting.append(pending[k]); k += 1
                    if not waiting:
                        clock = pending[k][0]
                        continue
                    if policy == "fifo":
                        waiting.sort(key=lambda o: o[0])
                    else:
                        waiting.sort(key=lambda o: (not o[2], o[0]))
                    arr, i, urgent, a, b = waiting.pop(0)
                    res[policy]["urgent" if urgent else "normal"].append(clock - arr)
                    clock += (dist[(pos, a)] + dist[(a, b)]) / speed + handling_s
                    pos = b
                    done += 1
        out[load_name] = {pol: {kind: dict(mean=st.mean(v), p90=sorted(v)[int(0.9 * len(v))],
                                            max=max(v), n=len(v))
                                for kind, v in d.items()} for pol, d in res.items()}
        f, p = out[load_name]["fifo"]["urgent"]["mean"], out[load_name]["priority"]["urgent"]["mean"]
        print(f"E3 {load_name}: urgent wait FIFO {f:.0f}s -> priority {p:.0f}s ({100*(f-p)/f:.0f}% less)")
    out["params"] = dict(trials=trials, n_orders=n_orders, urgent_frac=urgent_frac,
                         speed=speed, handling_s=handling_s)
    save("E3_dispatch.json", out)


# ------------------------------------------------------------------ E4
def track(path, noise=False, rng=None, dt=0.05, t_max=150.0, log=False):
    x, y = path[0]
    yaw = math.atan2(path[1][1] - y, path[1][0] - x)
    pid, seg, t = ctl.HeadingPID(), 0, 0.0
    xte, traj = [], []
    while t < t_max:
        meas = (x, y, yaw + (rng.gauss(0, math.radians(2)) if noise else 0.0))
        v, w, seg, arrived, cross = ctl.control_step(meas, path, seg, pid, dt)
        xte.append(abs(cross))
        if log:
            traj.append((t, x, y, cross))
        if arrived:
            return True, t, xte, traj, math.dist((x, y), path[-1])
        wl, wr = ctl.unicycle_to_wheels(v, w)
        if noise:   # 5 % random wheel slip
            wl *= 1 - abs(rng.gauss(0, 0.05))
            wr *= 1 - abs(rng.gauss(0, 0.05))
        v = (wl + wr) * ctl.WHEEL_RADIUS / 2
        w = (wr - wl) * ctl.WHEEL_RADIUS / ctl.TRACK
        x += v * math.cos(yaw) * dt
        y += v * math.sin(yaw) * dt
        yaw = ctl.wrap(yaw + w * dt)
        t += dt
    return False, t, xte, traj, math.dist((x, y), path[-1])


def e4():
    prm = PRM(seed=1).build()
    out = {}
    for label, noise in (("ideal", False), ("noise_and_slip", True)):
        rng = random.Random(5)
        rms, mx, times, arrived, final = [], [], [], 0, []
        for a, b in PAIRS:
            p = prm.query(L[a], L[b])
            ok, t, xte, _, fe = track(p, noise, rng)
            arrived += ok
            rms.append(math.sqrt(sum(e * e for e in xte) / len(xte)))
            mx.append(max(xte))
            times.append(t)
            final.append(fe)
        out[label] = dict(arrived=arrived, routes=len(PAIRS), rms_mean_m=st.mean(rms),
                          rms_max_m=max(rms), max_xte_m=max(mx), time_mean_s=st.mean(times),
                          final_err_mean_m=st.mean(final))
        print("E4", label, {k: round(v, 3) for k, v in out[label].items()})
    p = prm.query(L["pharmacy"], L["icu"])
    _, _, _, traj, _ = track(p, True, random.Random(5), log=True)
    out["example"] = dict(route="pharmacy -> icu", path=p, traj=traj[::2])
    save("E4_controller.json", out)


# ------------------------------------------------------------------ E5
def e5():
    # each blocker leaves a gap of at least 1.3 m, so a detour exists
    blockers = {"bed in upper corridor": (-1.9, 0.6, 0.5, 1.2),
                "trolleys in lower corridor": (-0.6, -3.4, 1.9, -2.6),
                "cleaning cart near ward 1": (0.3, 3.0, 1.9, 3.6)}
    rows = []
    for name, rect in blockers.items():
        base = PRM(seed=1).build()
        before = {pr: base.query(L[pr[0]], L[pr[1]]) for pr in PAIRS}
        t = time.perf_counter()
        nodes, edges = base.add_obstacle(rect)
        repair_ms = (time.perf_counter() - t) * 1000
        t = time.perf_counter()
        rebuilt = PRM(obstacles=hm.OBSTACLES + [rect], seed=1).build()
        rebuild_ms = (time.perf_counter() - t) * 1000
        ok, longer, collide_before = 0, [], 0
        for pr in PAIRS:
            after = base.query(L[pr[0]], L[pr[1]])
            b = before[pr]
            if b and not all(edge_free(u, v, base.cobs) for u, v in zip(b, b[1:])):
                collide_before += 1
            if after:
                ok += 1
                if b:
                    longer.append(plen(after) - plen(b))
        rows.append(dict(blocker=name, rect=rect, nodes_removed=nodes, edges_removed=edges,
                         repair_ms=repair_ms, rebuild_ms=rebuild_ms,
                         old_routes_now_blocked=collide_before, success_after=ok,
                         pairs=len(PAIRS), mean_extra_len_m=st.mean(longer)))
        print("E5", name, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in rows[-1].items()})
    save("E5_blocked.json", rows)


if __name__ == "__main__":
    e1(); e2(); e3(); e4(); e5()

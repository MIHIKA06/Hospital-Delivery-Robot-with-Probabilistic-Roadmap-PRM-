"""Make report figures from results/E*.json.   python3 -m experiments.make_figures"""

from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

R = "results"
C = {"uniform": "#9e9ac8", "bridge": "#fd8d3c", "door": "#2171b5", "prm": "#2171b5",
     "rrt": "#cb181d", "fifo": "#969696", "priority": "#2171b5"}
plt.rcParams.update({"font.family": "serif", "font.size": 11})


def load(n):
    with open(os.path.join(R, n)) as f:
        return json.load(f)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(R, name), dpi=200)
    plt.close(fig)
    print("saved", name)


def fig_samplers():
    rows = load("E1_samplers.json")
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for s in ("uniform", "bridge", "door"):
        r = [x for x in rows if x["sampler"] == s]
        ax.plot([x["n"] for x in r], [x["success_pct"] for x in r], "o-", color=C[s],
                label={"door": "door-seeded (ours)", "bridge": "bridge test", "uniform": "uniform"}[s])
    ax.set_xlabel("roadmap samples n")
    ax.set_ylabel("route success (%)")
    ax.set_ylim(0, 105)
    ax.grid(alpha=0.3)
    ax.legend()
    save(fig, "fig_success_vs_n.png")


def fig_prm_vs_rrt():
    d = load("E2_prm_vs_rrt.json")
    cu = d["cumulative"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    n = range(1, len(cu["prm"]) + 1)
    ax.plot(n, [v / 1000 for v in cu["prm"]], color=C["prm"], label="PRM (build once + queries)")
    ax.plot(n, [v / 1000 for v in cu["rrt"]], color=C["rrt"], label="RRT (new tree per order)")
    ax.set_xlabel("number of delivery orders")
    ax.set_ylabel("cumulative planning time (s)")
    ax.grid(alpha=0.3)
    ax.legend()
    save(fig, "fig_prm_vs_rrt.png")


def fig_dispatch():
    d = load("E3_dispatch.json")
    loads = ["low", "medium", "high"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    w = 0.2
    for k, (pol, kind) in enumerate([("fifo", "urgent"), ("priority", "urgent"),
                                     ("fifo", "normal"), ("priority", "normal")]):
        vals = [d[l][pol][kind]["mean"] for l in loads]
        ax.bar([i + (k - 1.5) * w for i in range(3)], vals, w, color=C[pol],
               alpha=1.0 if kind == "urgent" else 0.45,
               label=f"{'FCFS' if pol == 'fifo' else 'priority'} - {kind}")
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{l} load" for l in loads])
    ax.set_ylabel("mean waiting time (s)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=9)
    save(fig, "fig_dispatch_wait.png")


def fig_tracking():
    d = load("E4_controller.json")["example"]
    path, traj = d["path"], d["traj"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.8), gridspec_kw={"width_ratios": [1.1, 1]})
    a1.plot(*zip(*path), "k--o", ms=4, lw=1, label="PRM path")
    a1.plot([p[1] for p in traj], [p[2] for p in traj], color=C["prm"], lw=2, label="robot")
    a1.set_aspect("equal")
    a1.set_xlabel("x (m)")
    a1.set_ylabel("y (m)")
    a1.set_title("pharmacy → ICU (noise + slip)", fontsize=10)
    a1.legend(fontsize=9)
    a1.grid(alpha=0.3)
    a2.plot([p[0] for p in traj], [100 * p[3] for p in traj], color=C["prm"])
    a2.axhline(0, color="k", lw=0.6)
    a2.set_xlabel("time (s)")
    a2.set_ylabel("cross-track error (cm)")
    a2.grid(alpha=0.3)
    save(fig, "fig_tracking.png")


def boxes(ax, items, arrows):
    for name, (x, y, w, h, col) in items.items():
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=col, ec="k"))
        ax.text(x + w / 2, y + h / 2, name, ha="center", va="center", fontsize=9)
    for a, b, lab in arrows:
        (x0, y0, w0, h0, _), (x1, y1, w1, h1, _) = items[a], items[b]
        s = (x0 + w0, y0 + h0 / 2) if x1 > x0 + w0 - 1e-6 else (x0 + w0 / 2, y0)
        e = (x1, y1 + h1 / 2) if x1 > x0 + w0 - 1e-6 else (x1 + w1 / 2, y1 + h1)
        ax.annotate("", e, s, arrowprops=dict(arrowstyle="->", lw=1.2))
        if lab:
            ax.text((s[0] + e[0]) / 2, (s[1] + e[1]) / 2 + 0.12, lab, ha="center", fontsize=8,
                    style="italic")
    ax.axis("off")


def fig_architecture():
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    items = {
        "Staff\n(terminal)": (0.1, 1.6, 1.3, 0.8, "#f0f0f0"),
        "Command-line\nclient (shell)": (1.9, 1.6, 1.6, 0.8, "#c6dbef"),
        "Order queue\n(priority / FCFS)": (4.0, 2.5, 1.7, 0.8, "#c6dbef"),
        "Dispatcher\nthread": (4.0, 0.7, 1.7, 0.8, "#c6dbef"),
        "PRM planner\n(roadmap + A*)": (6.3, 2.5, 1.7, 0.8, "#c7e9c0"),
        "PID path\nfollower": (6.3, 0.7, 1.7, 0.8, "#fdd0a2"),
        "CoppeliaSim\nPioneer P3-DX": (8.5, 0.7, 1.4, 0.8, "#fcbba1"),
    }
    boxes(ax, items, [("Staff\n(terminal)", "Command-line\nclient (shell)", "commands")])
    def arrow(s, e, lab=""):
        ax.annotate("", e, s, arrowprops=dict(arrowstyle="->", lw=1.2))
        if lab:
            ax.text((s[0] + e[0]) / 2, (s[1] + e[1]) / 2 + 0.1, lab, ha="center", fontsize=8,
                    style="italic")
    arrow((3.5, 2.1), (4.0, 2.8), "deliver / cancel")
    arrow((3.5, 1.9), (4.0, 1.2), "stop / block")
    arrow((4.85, 2.5), (4.85, 1.5), "next order")
    arrow((5.7, 1.3), (6.3, 2.7), "plan(start, goal)")
    arrow((7.15, 2.5), (7.15, 1.5), "waypoints")
    arrow((8.0, 1.2), (8.5, 1.2), "")
    ax.text(8.25, 1.45, "wheel speeds", fontsize=8, ha="center", style="italic")
    arrow((8.5, 0.95), (5.7, 0.95), "")
    ax.text(7.1, 0.45, "robot pose (ZeroMQ remote API)", fontsize=8, ha="center", style="italic")
    ax.add_patch(FancyBboxPatch((1.9, 0.2), 1.6, 0.55, boxstyle="round,pad=0.02", fc="#ffffff",
                                ec="k", ls="--"))
    ax.text(2.7, 0.475, "order log (CSV)", ha="center", va="center", fontsize=9)
    arrow((4.0, 0.85), (3.5, 0.5), "")
    save(fig, "fig_architecture.png")


def fig_flowchart():
    fig, ax = plt.subplots(figsize=(5.2, 7.4))
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 10)
    steps = ["Start: floor plan, robot radius r, n, k",
             "Inflate obstacles by r (C-space)",
             "Seed nodes in and beside each door",
             "Sample uniform points; keep free ones\nuntil n nodes",
             "Connect each node to k nearest\n(edge collision-free, length ≤ 3 m)",
             "Roadmap ready (built once)",
             "Order: connect start & goal to roadmap",
             "A* search on roadmap",
             "Shortcut smoothing → waypoints"]
    y = 9.3
    for i, s in enumerate(steps):
        col = "#c7e9c0" if i < 6 else "#c6dbef"
        ax.add_patch(FancyBboxPatch((0.6, y - 0.35), 4.8, 0.7, boxstyle="round,pad=0.03",
                                    fc=col, ec="k"))
        ax.text(3, y, s, ha="center", va="center", fontsize=8.5)
        if i < len(steps) - 1:
            ax.annotate("", (3, y - 0.65), (3, y - 0.37), arrowprops=dict(arrowstyle="->"))
        y -= 1.05
    ax.text(5.55, 7.2, "learning\nphase", fontsize=8, rotation=90, va="center", color="#238b45")
    ax.text(5.55, 2.1, "query\nphase", fontsize=8, rotation=90, va="center", color="#2171b5")
    ax.axis("off")
    save(fig, "fig_flowchart.png")


if __name__ == "__main__":
    fig_samplers(); fig_prm_vs_rrt(); fig_dispatch(); fig_tracking(); fig_architecture(); fig_flowchart()

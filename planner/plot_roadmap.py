"""Draw the hospital map, the PRM roadmap and example routes (report figures).

    python3 -m planner.plot_roadmap                 # -> results/fig_roadmap_door.png
    python3 -m planner.plot_roadmap --sampler uniform
    python3 -m planner.plot_roadmap --block -1.9 -0.4 0.6 0.4
"""

from __future__ import annotations

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from client import config  # noqa: E402
from . import hospital_map as hm  # noqa: E402
from .prm import PRM  # noqa: E402

ROUTES = [("pharmacy", "icu"), ("lab", "ward1"), ("emergency", "ward2")]


def draw(prm: PRM, routes, title: str, out: str, extra=()):
    fig, ax = plt.subplots(figsize=(7, 7))
    for r in hm.WALLS:
        ax.add_patch(Rectangle(r[:2], r[2] - r[0], r[3] - r[1], color="#333333"))
    for r in hm.FURNITURE:
        ax.add_patch(Rectangle(r[:2], r[2] - r[0], r[3] - r[1], color="#a0a0a0"))
    for r in extra:
        ax.add_patch(Rectangle(r[:2], r[2] - r[0], r[3] - r[1], color="#d62728", alpha=0.7,
                               label="blocked area"))
    for i, nb in prm.adj.items():
        for j in nb:
            if j > i:
                (x0, y0), (x1, y1) = prm.nodes[i], prm.nodes[j]
                ax.plot([x0, x1], [y0, y1], color="#9ecae1", lw=0.4, zorder=1)
    xs, ys = zip(*[prm.nodes[i] for i in prm.adj])
    ax.scatter(xs, ys, s=4, color="#3182bd", zorder=2, label=f"roadmap ({len(prm.adj)} nodes)")
    colours = ["#e6550d", "#31a354", "#756bb1"]
    for (a, b), c in zip(routes, colours):
        path = prm.query(config.LOCATIONS[a], config.LOCATIONS[b])
        if path:
            px, py = zip(*path)
            ax.plot(px, py, color=c, lw=2.2, zorder=3, label=f"{a} → {b}")
    for name, (x, y) in config.LOCATIONS.items():
        ax.plot(x, y, "k*", ms=8, zorder=4)
        ax.annotate(name, (x, y), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set_xlim(hm.BOUNDS[0] - 0.3, hm.BOUNDS[2] + 0.3)
    ax.set_ylim(hm.BOUNDS[1] - 0.3, hm.BOUNDS[3] + 0.3)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=8)
    fig.tight_layout()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print("saved", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sampler", default="door", choices=["uniform", "bridge", "door"])
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--block", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    args = ap.parse_args()
    prm = PRM(n_samples=args.n, sampler=args.sampler, seed=args.seed).build()
    extra = []
    suffix = args.sampler
    if args.block:
        prm.add_obstacle(tuple(args.block))
        extra = [tuple(args.block)]
        suffix += "_blocked"
    draw(prm, ROUTES, f"PRM roadmap ({args.sampler} sampler, n={args.n})",
         f"results/fig_roadmap_{suffix}.png", extra)


if __name__ == "__main__":
    main()

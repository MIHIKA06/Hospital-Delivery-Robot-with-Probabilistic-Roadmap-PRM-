"""Render the open CoppeliaSim scene to a PNG with a temporary vision sensor
(for the report, or when you cannot screenshot the GUI).

    python3 tools/snapshot.py [--out results/fig_scene.png] [--top]
"""
import argparse, math, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="results/fig_scene.png")
ap.add_argument("--top", action="store_true", help="orthographic top-down view")
a = ap.parse_args()

sim = RemoteAPIClient().require("sim")
W, H = (1000, 1000) if a.top else (1400, 900)
cam = sim.createVisionSensor(3, [W, H, 0, 0], [0.05, 40, math.radians(55), 13.2, 0, 0, 0, 0.9, 0.9, 0.9, 0])
if a.top:
    sim.setObjectPosition(cam, sim.handle_world, [0, 0, 15])
    sim.setObjectOrientation(cam, sim.handle_world, [math.pi, 0, 0])
    sim.setObjectOrientation(cam, sim.handle_world, [math.pi, 0, math.pi])
else:
    C, T = np.array([0.0, -12.0, 11.0]), np.array([0.0, -0.8, 0.0])
    z = (T - C) / np.linalg.norm(T - C)                 # sensor looks along +z
    y = np.array([0.0, 0.0, 1.0]) - z[2] * z            # image up = world up
    y /= np.linalg.norm(y)
    x = np.cross(y, z)
    m = [x[0], y[0], z[0], C[0], x[1], y[1], z[1], C[1], x[2], y[2], z[2], C[2]]
    sim.setObjectMatrix(cam, sim.handle_world, [float(v) for v in m])
sim.handleVisionSensor(cam)
img, (w, h) = sim.getVisionSensorImg(cam)
sim.removeObjects([cam])
arr = np.frombuffer(img, dtype=np.uint8).reshape(h, w, 3)[::-1]
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
plt.imsave(a.out, arr)
print("saved", a.out)

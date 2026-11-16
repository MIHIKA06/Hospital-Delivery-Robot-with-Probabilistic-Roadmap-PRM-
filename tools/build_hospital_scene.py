"""Build the hospital scene scene/hospital.ttt in CoppeliaSim (Sumit's module).

Everything comes from planner/hospital_map.py, so the simulator and the PRM
planner always use the same floor plan:

  * every wall and furniture box becomes a static, respondable cuboid
    (the robot really collides with them),
  * every room gets a coloured floor tile so you can see the layout,
  * a Pioneer P3-DX named /PioneerP3DX is placed at "home", with its demo
    script removed (it would fight our controller),
  * one dummy /loc_<name> per location in client/config.py, which the client
    reads automatically.

Usage (CoppeliaSim running, any scene open; it is replaced):
    python3 tools/build_hospital_scene.py            # build + save scene/hospital.ttt
    python3 tools/build_hospital_scene.py --no-save  # build only
"""

import argparse
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from client import config  # noqa: E402
from planner import hospital_map as hm  # noqa: E402
from coppeliasim_zmqremoteapi_client import RemoteAPIClient  # noqa: E402

WALL_HEIGHT = 1.0
FURNITURE_HEIGHT = 0.7

# room floor tiles: name, rect, colour
ROOMS = [
    ("pharmacy", (-6.0, 0.0, -2.0, 6.0), [0.55, 0.80, 0.55]),
    ("lab",      (-6.0, -6.0, -2.0, 0.0), [0.55, 0.70, 0.90]),
    ("corridor", (-2.0, -6.0, 2.0, 6.0), [0.85, 0.85, 0.80]),
    ("ward1",    (2.0, 2.75, 6.0, 6.0), [0.95, 0.80, 0.55]),
    ("ward2",    (2.0, 0.0, 6.0, 2.75), [0.95, 0.75, 0.65]),
    ("ward3",    (2.0, -2.75, 6.0, 0.0), [0.95, 0.70, 0.75]),
    ("icu",      (2.0, -6.0, 6.0, -2.75), [0.95, 0.55, 0.55]),
]
WALL_COLOUR = [0.92, 0.92, 0.95]
FURNITURE_COLOUR = [0.45, 0.33, 0.25]
MARKER_COLOUR = [0.1, 0.3, 0.9]


def box(sim, rect, z0, height, colour, name, parent, respondable=True):
    x0, y0, x1, y1 = rect
    h = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [x1 - x0, y1 - y0, height], 0)
    sim.setObjectPosition(h, sim.handle_world, [(x0 + x1) / 2, (y0 + y1) / 2, z0 + height / 2])
    sim.setObjectInt32Param(h, sim.shapeintparam_static, 1)
    sim.setObjectInt32Param(h, sim.shapeintparam_respondable, 1 if respondable else 0)
    sim.setShapeColor(h, None, sim.colorcomponent_ambient_diffuse, colour)
    sim.setObjectAlias(h, name)
    sim.setObjectParent(h, parent, True)
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "scene", "hospital.ttt"))
    args = ap.parse_args()

    client = RemoteAPIClient(host=config.ZMQ_HOST, port=config.ZMQ_PORT)
    sim = client.require("sim") if hasattr(client, "require") else client.getObject("sim")
    sim.stopSimulation()
    while sim.getSimulationState() != sim.simulation_stopped:
        pass
    sim.closeScene()                       # start from the default empty scene (has a floor)

    root = sim.createDummy(0.01)
    sim.setObjectAlias(root, "Hospital")
    walls = sim.createDummy(0.01); sim.setObjectAlias(walls, "Walls"); sim.setObjectParent(walls, root, True)
    furn = sim.createDummy(0.01); sim.setObjectAlias(furn, "Furniture"); sim.setObjectParent(furn, root, True)
    floor = sim.createDummy(0.01); sim.setObjectAlias(floor, "Rooms"); sim.setObjectParent(floor, root, True)

    # The default scene floor is only 5 m x 5 m; the robot would drive off its
    # edge. Replace it with a respondable slab covering the whole hospital.
    try:
        sim.removeModel(sim.getObject("/Floor"))
    except Exception:
        pass
    b = hm.BOUNDS
    box(sim, (b[0] - 0.5, b[1] - 0.5, b[2] + 0.5, b[3] + 0.5), -0.1, 0.1,
        [0.6, 0.6, 0.6], "floor", root)
    for name, rect, colour in ROOMS:
        box(sim, rect, 0.0, 0.005, colour, f"floor_{name}", floor, respondable=False)
    for i, r in enumerate(hm.WALLS):
        box(sim, r, 0.0, WALL_HEIGHT, WALL_COLOUR, f"wall{i}", walls)
    for i, r in enumerate(hm.FURNITURE):
        box(sim, r, 0.0, FURNITURE_HEIGHT, FURNITURE_COLOUR, f"furniture{i}", furn)
    print(f"Built {len(hm.WALLS)} walls, {len(hm.FURNITURE)} furniture boxes, {len(ROOMS)} rooms.")

    # robot
    models = sim.getStringParam(sim.stringparam_resourcesdir) + "/models"
    robot = sim.loadModel(models + "/robots/mobile/pioneer p3dx.ttm")
    sim.setObjectAlias(robot, config.ROBOT_PATH.strip("/"))
    for s in sim.getObjectsInTree(robot, sim.sceneobject_script):
        sim.removeObjects([s])
    hx, hy = config.LOCATIONS["home"]
    z = sim.getObjectPosition(robot, sim.handle_world)[2]
    sim.setObjectPosition(robot, sim.handle_world, [hx, hy, z])
    sim.setObjectOrientation(robot, sim.handle_world, [0, 0, 0])
    print("Placed Pioneer P3-DX at home", (hx, hy))

    # location markers (thin discs so they are visible, plus the /loc_ dummies)
    for name, (x, y) in config.LOCATIONS.items():
        d = sim.createDummy(0.15)
        sim.setObjectAlias(d, f"loc_{name}")
        sim.setObjectPosition(d, sim.handle_world, [x, y, 0.05])
        disc = sim.createPrimitiveShape(sim.primitiveshape_cylinder, [0.35, 0.35, 0.01], 0)
        sim.setObjectInt32Param(disc, sim.shapeintparam_static, 1)
        sim.setObjectInt32Param(disc, sim.shapeintparam_respondable, 0)
        sim.setShapeColor(disc, None, sim.colorcomponent_ambient_diffuse, MARKER_COLOUR)
        sim.setObjectAlias(disc, f"marker_{name}")
        sim.setObjectPosition(disc, sim.handle_world, [x, y, 0.008])
        sim.setObjectParent(disc, d, True)
    print(f"Placed {len(config.LOCATIONS)} location dummies.")

    # aim the GUI camera at the whole floor (cameras look along their +z axis)
    try:
        import numpy as np
        cam = sim.getObject("/DefaultCamera")
        C, T = np.array([0.0, -12.0, 11.0]), np.array([0.0, -0.8, 0.0])
        zc = (T - C) / np.linalg.norm(T - C)
        yc = np.array([0.0, 0.0, 1.0]) - zc[2] * zc
        yc /= np.linalg.norm(yc)
        xc = np.cross(yc, zc)
        sim.setObjectMatrix(cam, sim.handle_world, [float(v) for v in (
            xc[0], yc[0], zc[0], C[0], xc[1], yc[1], zc[1], C[1], xc[2], yc[2], zc[2], C[2])])
    except Exception as e:
        print("(camera not moved:", e, ")")

    if not args.no_save:
        out = os.path.abspath(args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sim.saveScene(out)
        print("Saved", out)


if __name__ == "__main__":
    main()

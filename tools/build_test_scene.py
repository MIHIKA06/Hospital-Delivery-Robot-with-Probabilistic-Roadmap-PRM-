"""Build a minimal CoppeliaSim test scene for the command-line client.

Loads a Pioneer P3-DX, removes its built-in demo script (it would fight our
commands), and adds one dummy /loc_<name> per location in client/config.py so
the client reads coordinates from the scene. This is ONLY for testing the
client; the real hospital scene (walls, rooms) is Sumit's scene/hospital.ttt.

Usage (CoppeliaSim running):
    python3 tools/build_test_scene.py [--save scene/client_test.ttt]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from client import config  # noqa: E402
from coppeliasim_zmqremoteapi_client import RemoteAPIClient  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", help="save the scene to this .ttt path")
    args = ap.parse_args()

    client = RemoteAPIClient()
    sim = client.require("sim") if hasattr(client, "require") else client.getObject("sim")
    sim.stopSimulation()
    while sim.getSimulationState() != sim.simulation_stopped:
        pass

    # robot
    try:
        robot = sim.getObject(config.ROBOT_PATH)
        print("Robot already in scene.")
    except Exception:
        models = sim.getStringParam(sim.stringparam_resourcesdir) + "/models"
        robot = sim.loadModel(models + "/robots/mobile/pioneer p3dx.ttm")
        sim.setObjectAlias(robot, config.ROBOT_PATH.strip("/"))
        print("Loaded Pioneer P3-DX.")
    for s in sim.getObjectsInTree(robot, sim.sceneobject_script):
        sim.removeObjects([s])
        print("Removed built-in robot script.")
    hx, hy = config.LOCATIONS["home"]
    z = sim.getObjectPosition(robot, sim.handle_world)[2]
    sim.setObjectPosition(robot, sim.handle_world, [hx, hy, z])

    # location markers
    for name, (x, y) in config.LOCATIONS.items():
        try:
            h = sim.getObject(f"/loc_{name}")
        except Exception:
            h = sim.createDummy(0.15)
            sim.setObjectAlias(h, f"loc_{name}")
        sim.setObjectPosition(h, sim.handle_world, [x, y, 0.05])
    print(f"Placed {len(config.LOCATIONS)} location dummies.")

    if args.save:
        path = os.path.abspath(args.save)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sim.saveScene(path)
        print("Saved", path)


if __name__ == "__main__":
    main()

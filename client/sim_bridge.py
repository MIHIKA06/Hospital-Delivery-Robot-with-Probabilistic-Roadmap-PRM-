"""Connection to the robot.

RealBridge   - talks to CoppeliaSim through the ZeroMQ remote API.
DryRunBridge - a fake robot for testing the client without CoppeliaSim.

Both expose: connect(), pose(), drive(path, should_stop), scene_locations(), close().
Every method must be called from the SAME thread (the dispatcher thread),
because the ZeroMQ client is not thread-safe.
"""

from __future__ import annotations

import math
import time
from typing import Dict, Tuple

from . import config
from .interfaces import load_follower

Point = Tuple[float, float]


class RealBridge:
    name = "CoppeliaSim (ZeroMQ remote API)"

    def __init__(self, host: str = config.ZMQ_HOST, port: int = config.ZMQ_PORT):
        self.host, self.port = host, port
        self.sim = None
        self.robot = None
        self.follow, self.follower_name = load_follower()

    def connect(self) -> None:
        try:
            from coppeliasim_zmqremoteapi_client import RemoteAPIClient
        except ImportError as e:
            raise RuntimeError("Install the client first: "
                               "pip install coppeliasim-zmqremoteapi-client") from e
        client = RemoteAPIClient(host=self.host, port=self.port)
        # newer API uses require(), older uses getObject()
        self.sim = client.require("sim") if hasattr(client, "require") else client.getObject("sim")
        self.robot = self.sim.getObject(config.ROBOT_PATH)
        if self.sim.getSimulationState() == self.sim.simulation_stopped:
            self.sim.startSimulation()

    def scene_locations(self) -> Dict[str, Point]:
        """Read dummies named /loc_<name> from the scene, if any."""
        found = {}
        for name in config.LOCATIONS:
            try:
                h = self.sim.getObject(f"/loc_{name}")
            except Exception:
                continue
            x, y, _ = self.sim.getObjectPosition(h, self.sim.handle_world)
            found[name] = (x, y)
        return found

    def pose(self) -> Tuple[float, float, float]:
        x, y, _ = self.sim.getObjectPosition(self.robot, self.sim.handle_world)
        yaw = self.sim.getObjectOrientation(self.robot, self.sim.handle_world)[2]
        return x, y, yaw

    def drive(self, path, should_stop) -> bool:
        return bool(self.follow(self.sim, self.robot, path, should_stop))

    def close(self) -> None:
        if self.sim is not None:
            try:
                self.sim.stopSimulation()
            except Exception:
                pass


class DryRunBridge:
    """Pretend robot that moves along the path at `speed` m/s (time-scaled)."""
    name = "DRY RUN (no simulator)"
    follower_name = "simulated motion"

    def __init__(self, speed: float = 0.8, time_scale: float = 0.05):
        self.x, self.y, self.yaw = config.LOCATIONS["home"] + (0.0,)
        self.speed, self.time_scale = speed, time_scale

    def connect(self) -> None:
        pass

    def scene_locations(self) -> Dict[str, Point]:
        return {}

    def pose(self):
        return self.x, self.y, self.yaw

    def drive(self, path, should_stop) -> bool:
        for a, b in zip(path, path[1:]):
            steps = max(1, int(math.dist(a, b) / 0.1))
            self.yaw = math.atan2(b[1] - a[1], b[0] - a[0])
            for i in range(1, steps + 1):
                if should_stop():
                    return False
                t = i / steps
                self.x, self.y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
                time.sleep(0.1 / self.speed * self.time_scale)
        return True

    def close(self) -> None:
        pass

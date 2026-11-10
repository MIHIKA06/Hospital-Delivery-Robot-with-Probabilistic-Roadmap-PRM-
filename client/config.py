"""Named locations on the hospital floor and connection settings.

Coordinates are (x, y) in metres in the CoppeliaSim world frame.
These are PLACEHOLDERS - update them to match the final hospital scene
(scene/hospital.ttt). If the scene contains dummy objects named
/loc_<name> (e.g. /loc_pharmacy), the real client reads their positions
automatically and overrides the values below.
"""

LOCATIONS = {
    "home":      (0.0, 0.0),    # robot charging / parking bay
    "pharmacy":  (-4.0, 3.0),
    "lab":       (-4.0, -3.0),
    "reception": (0.0, -4.0),
    "ward1":     (4.0, 4.0),
    "ward2":     (4.0, 1.5),
    "ward3":     (4.0, -1.5),
    "icu":       (4.0, -4.0),
    "emergency": (-1.5, 4.5),
}

# Name of the robot model in the scene (Sumit's scene).
ROBOT_PATH = "/PioneerP3DX"

# ZeroMQ remote API defaults (CoppeliaSim listens on 23000).
ZMQ_HOST = "localhost"
ZMQ_PORT = 23000

# Where every completed/failed order is logged (used by Prachi for results).
ORDER_LOG_CSV = "results/order_log.csv"

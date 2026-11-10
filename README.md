# Hospital Delivery Robot with Probabilistic Roadmap (PRM)

CSAI4014 AISR, Project P05, Group G06, Batch B1.
Platform: CoppeliaSim (OMPL plugin) + Python command-line client via the ZeroMQ remote API.

Building a PRM over a hospital floor plan and planning routes between the wards and the pharmacy. Delivery orders are sent to the robot from a Python command-line client.

## Team and modules

| Member | SAP ID | Module | Folder |
|---|---|---|---|
| Mihika | 500122055 | Command-line client, order queue, ZeroMQ link, integration | `client/` |
| Divyanshu Dhyani | 500122522 | Baseline planner (RRT / A*) and benchmarking | `baseline/` |
| Disha Rastogi | 500119681 | PRM planner | `planner/` |
| Sumit Malhotra | 500123752 | Hospital scene, robot, path-following controller | `scene/`, `controller/` |
| Prachi Chetan Padodara | 500126371 | Experiments, plots, result tables | `results/` |

## Setup

```bash
pip install -r requirements.txt
```

## Run

From this folder:

```bash
python3 -m client --dry-run                              # test without CoppeliaSim
python3 -m client                                        # CoppeliaSim running with scene/hospital.ttt open
python3 -m client --dry-run --batch examples_orders.txt  # scripted orders (for experiments)
```

Shell commands: `deliver <pickup> <dropoff> [--urgent] [--item NAME]`, `status`, `queue`,
`history`, `cancel <id>`, `stop` (emergency stop), `resume`, `locations`, `wait`, `quit`.

Each finished order is appended to `results/order_log.csv` with wait time, run time, planning time and path length.

## Interfaces between modules

- **`planner/prm.py`** must provide `plan(start, goal) -> list[(x, y)] | None`.
- **`controller/controller.py`** must provide `follow(sim, robot_handle, path, should_stop) -> bool`.
- **Scene**: the robot is named `/PioneerP3DX`. Optional dummies `/loc_pharmacy`, `/loc_ward1`, ... set the location coordinates. Otherwise the client uses `client/config.py`.

Until those files exist, the client falls back to a straight-line planner and a kinematic follower, so it always runs.

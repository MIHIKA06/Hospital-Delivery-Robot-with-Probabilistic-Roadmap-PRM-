# Hospital Delivery Robot with Probabilistic Roadmap (PRM)

CSAI4014 AISR, Project P05, Group G06, Batch B1.
Platform: CoppeliaSim (OMPL plugin) + Python command-line client via the ZeroMQ remote API.

Building a PRM over a hospital floor plan and planning routes between the wards and the pharmacy. Delivery orders are sent to the robot from a Python command-line client.

## Team and modules

| Member | SAP ID | Module | Folder |
|---|---|---|---|
| Mihika | 500122055 | Command-line client, order queue, ZeroMQ link, integration; PRM planner code | `client/`, `planner/` |
| Divyanshu Dhyani | 500122522 | Baseline planner (RRT / A*) and benchmarking | `baseline/` |
| Disha Rastogi | 500119681 | PRM planner (code written by Mihika while Disha was unwell; Disha's new tasks below) | `planner/` |
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

### Testing with CoppeliaSim (tested with CoppeliaSim Edu 4.10, macOS arm64)

1. Start CoppeliaSim. The ZeroMQ remote API server starts automatically on port 23000.
2. Open `scene/client_test.ttt`, or build it with `python3 tools/build_test_scene.py`. It contains a Pioneer P3-DX with its demo script removed and one `/loc_<name>` dummy per location.
3. Run `python3 -m client`. Orders now move the robot in the simulator.

`scene/client_test.ttt` is only for testing the client. The real hospital scene with walls and rooms will be `scene/hospital.ttt`.

Shell commands: `deliver <pickup> <dropoff> [--urgent] [--item NAME]`, `status`, `queue`,
`history`, `cancel <id>`, `stop` (emergency stop), `resume`, `block <x0> <y0> <x1> <y1>` (mark an area blocked; the PRM re-plans around it), `locations`, `wait`, `quit`.

Each finished order is appended to `results/order_log.csv` with wait time, run time, planning time and path length.

## PRM planner (`planner/`)

- `hospital_map.py` is the 12 m x 12 m floor plan: pharmacy, lab, 3 wards, ICU, corridor, furniture and 1.0 m doors. **Sumit's CoppeliaSim scene must be built from this map.**
- `prm.py` covers the learning phase (sampling plus k-nearest connection, k = 10, max edge 3 m) and the query phase (A*, then shortcut smoothing). The robot is a disc of radius 0.30 m, and obstacles are inflated by that radius.
- It has three samplers: `uniform`, `bridge` (the bridge test of Hsu et al.) and `door` (the default). The door sampler seeds nodes in and beside each doorway.
- `add_obstacle` / `block` remove the roadmap nodes and edges a new obstacle invalidates, without rebuilding the roadmap.
- `python3 -m planner.test_prm` runs the sanity tests.
- `python3 -m planner.plot_roadmap [--sampler uniform|bridge|door] [--block x0 y0 x1 y1]` writes `results/fig_roadmap_*.png`.

First measurements: all 72 ordered location pairs, 10 seeds per setting.

| Sampler | n = 300, mean success | Seeds with 100% of pairs connected |
|---|---|---|
| uniform | 53.9% | 0/10 |
| bridge | 83.3% | 5/10 |
| door | 100% (also at n = 100) | 10/10 |

Query time is under 1 ms per route, and building the roadmap takes about 30 ms.

## Interfaces between modules

- **`planner/prm.py`** must provide `plan(start, goal) -> list[(x, y)] | None`.
- **`controller/controller.py`** must provide `follow(sim, robot_handle, path, should_stop) -> bool`.
- **Scene**: the robot is named `/PioneerP3DX`. Optional dummies `/loc_pharmacy`, `/loc_ward1`, ... set the location coordinates. Otherwise the client uses `client/config.py`.

Until those files exist, the client falls back to a straight-line planner and a kinematic follower, so it always runs.

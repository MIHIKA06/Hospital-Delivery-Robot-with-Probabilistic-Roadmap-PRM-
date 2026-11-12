"""Hospital delivery robot - command-line client.

Run from the repository root:

    python -m client --dry-run          # no simulator needed
    python -m client                    # connect to CoppeliaSim on localhost:23000
    python -m client --batch orders.txt # run commands from a file (for experiments)

Type `help` inside the shell for the list of commands.
"""

from __future__ import annotations

import argparse
import cmd
import math
import shlex
import sys
import time

from . import config
from .dispatcher import Dispatcher
from .orders import PRIORITY_NAMES, PRIORITY_NORMAL, PRIORITY_URGENT, OrderQueue
from .sim_bridge import DryRunBridge, RealBridge


class HospitalShell(cmd.Cmd):
    intro = ("\nHospital Delivery Robot - command client\n"
             "Type 'help' for commands, 'locations' to see where the robot can go.\n")
    prompt = "hospital> "

    def __init__(self, queue: OrderQueue, dispatcher: Dispatcher, **kw):
        super().__init__(**kw)
        self.queue = queue
        self.dispatcher = dispatcher

    # ---------- helpers ----------
    def _check_location(self, name: str) -> bool:
        if name not in self.dispatcher.locations:
            print(f"Unknown location '{name}'. Known: {', '.join(sorted(self.dispatcher.locations))}")
            return False
        return True

    def emptyline(self):  # don't repeat the last command on Enter
        pass

    def precmd(self, line):
        line = line.split("#", 1)[0].strip()   # allow comments in batch files
        if line and not self.use_rawinput:
            print(f"> {line}")
        return line

    def default(self, line):
        print(f"Unknown command: {line.split()[0]}. Type 'help'.")

    # ---------- commands ----------
    def do_deliver(self, arg):
        """deliver <pickup> <dropoff> [--urgent] [--item NAME]
        Queue a delivery, e.g.  deliver pharmacy ward3 --urgent --item insulin"""
        p = argparse.ArgumentParser(prog="deliver", add_help=False)
        p.add_argument("pickup")
        p.add_argument("dropoff")
        p.add_argument("--urgent", action="store_true")
        p.add_argument("--item", default="package")
        try:
            a = p.parse_args(shlex.split(arg))
        except SystemExit:
            print("usage: deliver <pickup> <dropoff> [--urgent] [--item NAME]")
            return
        if not (self._check_location(a.pickup) and self._check_location(a.dropoff)):
            return
        if a.pickup == a.dropoff:
            print("Pickup and dropoff are the same place.")
            return
        prio = PRIORITY_URGENT if a.urgent else PRIORITY_NORMAL
        order = self.queue.add(a.pickup, a.dropoff, prio, a.item)
        print(f"Queued order #{order.order_id} [{PRIORITY_NAMES[prio]}] "
              f"{a.item}: {a.pickup} -> {a.dropoff}")
        if self.dispatcher.stopped:
            print("Note: robot is in EMERGENCY STOP. Type 'resume' to continue.")

    def complete_deliver(self, text, line, begidx, endidx):
        return [n for n in self.dispatcher.locations if n.startswith(text)]

    def do_status(self, arg):
        """status - robot position, current order and queue length"""
        x, y, yaw = self.dispatcher.last_pose
        state = "EMERGENCY STOP" if self.dispatcher.stopped else (
            "busy" if self.dispatcher.current else "idle")
        print(f"Robot:   ({x:.2f}, {y:.2f}) m, heading {math.degrees(yaw):.0f} deg - {state}")
        cur = self.dispatcher.current
        print(f"Current: {cur.summary() if cur else '-'}")
        print(f"Queued:  {len(self.queue.pending())} order(s)")

    def do_queue(self, arg):
        """queue - list waiting orders in the order they will be served"""
        pending = self.queue.pending()
        if not pending:
            print("Queue is empty.")
        for o in pending:
            print("  " + o.summary())

    def do_history(self, arg):
        """history - all orders created in this session"""
        for o in self.queue.history:
            print("  " + o.summary())

    def do_cancel(self, arg):
        """cancel <order_id> - remove a waiting order from the queue"""
        try:
            oid = int(arg)
        except ValueError:
            print("usage: cancel <order_id>")
            return
        print(f"Order #{oid} cancelled." if self.queue.cancel(oid)
              else f"Order #{oid} is not waiting in the queue.")

    def do_stop(self, arg):
        """stop - EMERGENCY STOP: halt the robot now; current order fails"""
        self.dispatcher.emergency_stop()
        print("EMERGENCY STOP sent. Type 'resume' to continue with the queue.")

    def do_resume(self, arg):
        """resume - clear emergency stop and continue serving the queue"""
        self.dispatcher.resume()
        print("Resumed.")

    def do_block(self, arg):
        """block <x0> <y0> <x1> <y1> - mark a rectangle as blocked (e.g. a bed in the
        corridor); the PRM drops the affected nodes/edges and later routes avoid it"""
        try:
            x0, y0, x1, y1 = map(float, arg.split())
        except ValueError:
            print("usage: block <x0> <y0> <x1> <y1>   (metres, world frame)")
            return
        try:
            from planner.prm import block
        except ImportError:
            print("Blocking needs the PRM planner (planner/prm.py).")
            return
        rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        nodes, edges = block(rect)
        print(f"Blocked {rect}: removed {nodes} roadmap nodes and {edges} edges. "
              "Next routes will avoid it.")

    def do_locations(self, arg):
        """locations - list named places and their coordinates"""
        for name, (x, y) in sorted(self.dispatcher.locations.items()):
            print(f"  {name:<10} ({x:6.2f}, {y:6.2f})")

    def do_wait(self, arg):
        """wait - block until all queued orders are finished (useful in --batch files)"""
        while self.queue.pending() or self.dispatcher.current:
            if self.dispatcher.stopped:
                print("Robot is stopped; not waiting.")
                return
            time.sleep(0.2)

    def do_sleep(self, arg):
        """sleep <seconds> - pause (useful in --batch files)"""
        time.sleep(float(arg or 1))

    def do_quit(self, arg):
        """quit - stop the client"""
        self.dispatcher.shutdown()
        return True

    do_exit = do_quit
    do_EOF = do_quit


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Hospital delivery robot command client")
    ap.add_argument("--dry-run", action="store_true", help="fake robot, no CoppeliaSim needed")
    ap.add_argument("--host", default=config.ZMQ_HOST)
    ap.add_argument("--port", type=int, default=config.ZMQ_PORT)
    ap.add_argument("--batch", help="file with one shell command per line")
    ap.add_argument("--log", default=config.ORDER_LOG_CSV, help="CSV log of orders")
    args = ap.parse_args(argv)

    bridge = DryRunBridge() if args.dry_run else RealBridge(args.host, args.port)
    queue = OrderQueue()
    dispatcher = Dispatcher(queue, bridge, args.log)
    dispatcher.start()
    dispatcher.ready.wait()
    if dispatcher.error:
        print(f"Could not connect: {dispatcher.error}\n"
              "Is CoppeliaSim running with the scene loaded? Or use --dry-run.")
        return 1

    print(f"Robot link : {bridge.name}")
    print(f"Planner    : {dispatcher.planner_name}")
    print(f"Follower   : {bridge.follower_name}")
    print(f"Order log  : {args.log}")

    if args.batch:
        shell = HospitalShell(queue, dispatcher, stdin=open(args.batch))
        shell.use_rawinput = False
        shell.prompt = ""
        shell.intro = None
        shell.cmdloop()
        dispatcher.shutdown()
    else:
        shell = HospitalShell(queue, dispatcher)
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            dispatcher.shutdown()
    dispatcher.join(timeout=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())

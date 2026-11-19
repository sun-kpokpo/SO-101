"""Read-only check of both SO-101 arms (nothing moves).

Pings every motor and compares leader vs follower joint angles. Run through
`bash start_teleop.sh --check`.
"""

import os
from pathlib import Path

from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

KIT = Path(__file__).resolve().parent
# Set by start_teleop.sh (found from the boards' serial numbers)
FOLLOWER_PORT = os.environ["FOLLOWER_PORT"]
LEADER_PORT = os.environ["LEADER_PORT"]

arms = {
    "follower": SO101Follower(
        SO101FollowerConfig(port=FOLLOWER_PORT, id="my_follower_arm", calibration_dir=KIT / "calibration")
    ),
    "leader": SO101Leader(SO101LeaderConfig(port=LEADER_PORT, id="my_leader_arm", calibration_dir=KIT / "calibration")),
}

all_ok = True
angles = {}
for name, arm in arms.items():
    bus = arm.bus
    bus.connect(handshake=False)
    found = bus.broadcast_ping(num_retry=3) or {}
    missing = [m for m, motor in bus.motors.items() if motor.id not in found]
    if missing:
        all_ok = False
        print(f"{name:9s} MISSING motors: {missing} -> check power supply and the 3-pin cables of that arm")
    else:
        print(f"{name:9s} all 6 motors answer")
        bus.calibration = arm.calibration
        angles[name] = bus.sync_read("Present_Position")
    bus.port_handler.closePort()

if len(angles) == 2:
    print(f"\n{'joint':14s}{'leader':>9s}{'follower':>10s}")
    for joint, lead in angles["leader"].items():
        print(f"{joint:14s}{lead:9.1f}{angles['follower'][joint]:10.1f}")

print("\nREADY: run  bash start_teleop.sh" if all_ok else "\nNOT READY: fix the problem above, then check again.")

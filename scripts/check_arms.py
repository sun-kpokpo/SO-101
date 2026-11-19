"""Read-only health check for both SO-101 arms.

Pings every motor on each board and prints leader vs follower joint angles
(using the saved calibrations). Torque is never enabled, so nothing moves.
Do not run while lerobot-teleoperate / lerobot-record is using the ports.

    conda activate lerobot
    python ~/SO-101/scripts/check_arms.py
"""

from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

FOLLOWER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B048489-if00"
LEADER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B047977-if00"

arms = {
    "follower": SO101Follower(SO101FollowerConfig(port=FOLLOWER_PORT, id="my_follower_arm")),
    "leader": SO101Leader(SO101LeaderConfig(port=LEADER_PORT, id="my_leader_arm")),
}

angles = {}
for name, arm in arms.items():
    bus = arm.bus
    bus.connect(handshake=False)
    found = bus.broadcast_ping(num_retry=3) or {}
    missing = [m for m, motor in bus.motors.items() if motor.id not in found]
    print(f"{name:9s} motors found: {sorted(found)}" + (f"  MISSING: {missing}" if missing else "  OK"))
    if not missing:
        bus.calibration = arm.calibration
        angles[name] = bus.sync_read("Present_Position")
    bus.port_handler.closePort()

if len(angles) == 2:
    print(f"\n{'joint':14s}{'leader':>9s}{'follower':>10s}{'diff':>8s}")
    for joint, lead in angles["leader"].items():
        foll = angles["follower"][joint]
        print(f"{joint:14s}{lead:9.1f}{foll:10.1f}{foll - lead:8.1f}")
    print("\nAngles in degrees (gripper in 0-100 %). Same pose on both arms -> diffs should be a few degrees.")

"""Power test: teleoperate while logging the follower motors' supply voltage.

Shows the lowest motor voltage live and writes every reading to a CSV. If the follower drops out
("There is no status packet"), it then watches the motors for a few seconds:
  - motors answer again by themselves, with torque OFF  -> they rebooted = power dip (brownout)
  - motors stay silent                                   -> power lost / cable / board problem
No camera, no dataset. Put both arms in the same pose before starting. Stop with Ctrl+C.

    conda activate lerobot
    python ~/SO-101/scripts/power_test.py
"""

import time
from datetime import datetime
from pathlib import Path

from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

FOLLOWER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B048489-if00"
LEADER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B047977-if00"
FPS = 30

log_dir = Path.home() / "SO-101/power_logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / f"power_test_{datetime.now():%Y%m%d_%H%M%S}.csv"
log = open(log_path, "w", buffering=1)  # line-buffered: nothing lost on a crash

robot = SO101Follower(SO101FollowerConfig(port=FOLLOWER_PORT, id="my_follower_arm"))
teleop = SO101Leader(SO101LeaderConfig(port=LEADER_PORT, id="my_leader_arm"))
motors = list(robot.bus.motors)
log.write("time,event,min_v," + ",".join(motors) + "\n")


def volts() -> list[float]:
    raw = robot.bus.sync_read("Present_Voltage", normalize=False, num_retry=0)
    return [raw[m] / 10 for m in motors]


teleop.connect()
robot.connect()
print(f"Logging to {log_path}\nMove the leader: calm first, then faster. Ctrl+C to stop.\n")

history: list[tuple[float, float]] = []
lowest = 99.0
try:
    while True:
        t0 = time.perf_counter()
        try:
            v = volts()
        except ConnectionError:
            log.write(f"{time.time():.3f},voltage_read_failed,,\n")  # one lost packet is not a crash
        else:
            lowest = min(lowest, min(v))
            history = (history + [(time.time(), min(v))])[-FPS * 2 :]  # last 2 s
            log.write(f"{time.time():.3f},ok,{min(v):.1f}," + ",".join(f"{x:.1f}" for x in v) + "\n")
            print(f"\rmin motor voltage now {min(v):.1f} V   lowest so far {lowest:.1f} V   ", end="", flush=True)

        robot.get_observation()
        robot.send_action(teleop.get_action())
        time.sleep(max(0.0, 1 / FPS - (time.perf_counter() - t0)))

except KeyboardInterrupt:
    print(f"\n\nStopped. Lowest voltage seen: {lowest:.1f} V. Log: {log_path}")

except Exception as e:  # noqa: BLE001 - the dropout is what we are testing
    crash = time.time()
    log.write(f"{crash:.3f},CRASH {type(e).__name__},,\n")
    print(f"\n\nFOLLOWER DROPPED OUT: {type(e).__name__}: {e}")
    print("Voltage over the last 2 s before the dropout (oldest -> newest):")
    print("  " + " ".join(f"{v:.1f}" for _, v in history[-30:]))

    print("\nWatching the motors for 5 s (don't touch the arms)...")
    for _ in range(25):
        time.sleep(0.2)
        try:
            found = robot.bus.broadcast_ping(num_retry=0) or {}
        except Exception:  # noqa: BLE001
            found = {}
        line = f"+{time.time() - crash:4.1f}s  motors answering: {sorted(found)}"
        if len(found) == len(motors):
            torque = robot.bus.sync_read("Torque_Enable", normalize=False, num_retry=1)
            line += f"  torque on: {[m for m in motors if torque[m]]}  voltage: {min(volts()):.1f} V"
        print(line)
        log.write(f"{time.time():.3f},after_crash,,{line}\n")
        if len(found) == len(motors):
            break

    print(f"\nLowest voltage seen while running: {lowest:.1f} V. Log: {log_path}")

finally:
    for dev in (robot, teleop):
        try:
            dev.disconnect()
        except Exception:  # noqa: BLE001 - motors may still be resetting
            pass

"""`lerobot-record` + a log of the follower motors' supply voltage, to diagnose power-related crashes.

Same arguments as `lerobot-record`. Every control step it also reads `Present_Voltage` of the 6
follower motors (~1 ms) and appends `time, min V, max V, per-motor V` to a CSV. If the follower crashes
with "There is no status packet", the last lines show whether the voltage dropped just before.

    conda activate lerobot
    python ~/SO-101/scripts/record_power_log.py <same arguments as lerobot-record>
    # log: ~/SO-101/power_logs/power_<date>.csv
"""

import time
from datetime import datetime
from pathlib import Path

from lerobot.robots.so_follower.so_follower import SOFollower
from lerobot.scripts import lerobot_record

LOG_DIR = Path.home() / "SO-101/power_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_path = LOG_DIR / f"power_{datetime.now():%Y%m%d_%H%M%S}.csv"
log = open(log_path, "w", buffering=1)  # line-buffered: survives a crash
log.write("time,min_v,max_v,shoulder_pan,shoulder_lift,elbow_flex,wrist_flex,wrist_roll,gripper\n")
print(f"Power log: {log_path}")

_get_observation = SOFollower.get_observation


def get_observation_with_power(self):
    try:
        volts = self.bus.sync_read("Present_Voltage", normalize=False, num_retry=0)
        v = [volts[m] / 10 for m in self.bus.motors]
        log.write(f"{time.time():.3f},{min(v):.1f},{max(v):.1f}," + ",".join(f"{x:.1f}" for x in v) + "\n")
    except Exception as e:  # noqa: BLE001 - a failed read is exactly what we want to record
        log.write(f"{time.time():.3f},READ_FAILED,{type(e).__name__}\n")
    return _get_observation(self)


SOFollower.get_observation = get_observation_with_power

if __name__ == "__main__":
    lerobot_record.main()

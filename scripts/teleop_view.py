"""Teleoperate the SO-101 with a live view of the top camera.

Same control loop as `lerobot-teleoperate`, but the camera image is shown in a
lightweight ffplay window instead of Rerun (Rerun is too heavy for this laptop).

    conda activate lerobot
    python ~/SO-101/scripts/teleop_view.py
    python ~/SO-101/scripts/teleop_view.py --save-reference ~/SO-101/reference.png   # save last frame on exit
    python ~/SO-101/scripts/teleop_view.py --overlay ~/SO-101/reference.png          # blend a reference image (camera re-alignment)

Put both arms in the same pose before starting. Stop with Ctrl+C.
"""

import argparse
import subprocess
import time

import cv2
import numpy as np

from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

FOLLOWER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B048489-if00"
LEADER_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B047977-if00"
TOP_CAM = "/dev/v4l/by-id/usb-046d_Brio_100_2415AP0MU0J8-video-index0"
WIDTH, HEIGHT, FPS = 640, 480, 30

parser = argparse.ArgumentParser()
parser.add_argument("--overlay", help="reference image blended over the live view")
parser.add_argument("--alpha", type=float, default=0.5, help="overlay opacity (0-1)")
parser.add_argument("--save-reference", help="save the last camera frame here on exit")
args = parser.parse_args()

overlay = None
if args.overlay:
    overlay = cv2.cvtColor(cv2.imread(args.overlay), cv2.COLOR_BGR2RGB)
    overlay = cv2.resize(overlay, (WIDTH, HEIGHT))

robot = SO101Follower(
    SO101FollowerConfig(
        port=FOLLOWER_PORT,
        id="my_follower_arm",
        cameras={"top": OpenCVCameraConfig(index_or_path=TOP_CAM, width=WIDTH, height=HEIGHT, fps=FPS)},
    )
)
teleop = SO101Leader(SO101LeaderConfig(port=LEADER_PORT, id="my_leader_arm"))

viewer = subprocess.Popen(
    [
        "ffplay", "-loglevel", "error", "-window_title", "top camera",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", str(FPS), "-fflags", "nobuffer", "-flags", "low_delay", "-",
    ],
    stdin=subprocess.PIPE,
)

teleop.connect()
robot.connect()
frame = None
print("Teleop running at 30 Hz. Ctrl+C to stop.")
try:
    while True:
        t0 = time.perf_counter()
        obs = robot.get_observation()
        robot.send_action(teleop.get_action())

        frame = obs["top"]
        shown = frame if overlay is None else cv2.addWeighted(frame, 1 - args.alpha, overlay, args.alpha, 0)
        try:
            viewer.stdin.write(np.ascontiguousarray(shown, dtype=np.uint8).tobytes())
        except BrokenPipeError:
            pass  # viewer window closed: keep teleoperating without it

        time.sleep(max(0.0, 1 / FPS - (time.perf_counter() - t0)))
except KeyboardInterrupt:
    pass
finally:
    if args.save_reference and frame is not None:
        cv2.imwrite(args.save_reference, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        print("Reference frame saved to", args.save_reference)
    robot.disconnect()
    teleop.disconnect()
    viewer.terminate()

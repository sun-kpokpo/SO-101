"""Check, view and align the top camera — no arms needed.

Opens the camera exactly like the recording does (640x480 @ 30 fps), prints the measured frame
rate, then shows a live view in an ffplay window. Optional reference overlay to re-align the camera
(e.g. at the demo venue) and a centre grid. Stop with Ctrl+C or by closing the window.

    conda activate lerobot
    python ~/SO-101/scripts/camera_check.py                                   # check + live view
    python ~/SO-101/scripts/camera_check.py --overlay ~/SO-101/reference.png  # align on the reference
    python ~/SO-101/scripts/camera_check.py --save ~/SO-101/reference.png     # save last frame on exit
    python ~/SO-101/scripts/camera_check.py --list                            # list cameras and exit
"""

import argparse
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

TOP_CAM = "/dev/v4l/by-id/usb-046d_Brio_100_2415AP0MU0J8-video-index0"
WIDTH, HEIGHT, FPS = 640, 480, 30

parser = argparse.ArgumentParser()
parser.add_argument("--cam", default=TOP_CAM, help="camera path or index")
parser.add_argument("--overlay", help="reference image blended over the live view")
parser.add_argument("--alpha", type=float, default=0.5, help="overlay opacity (0-1)")
parser.add_argument("--grid", action="store_true", help="draw a 3x3 grid")
parser.add_argument("--save", help="save the last frame here on exit")
parser.add_argument("--list", action="store_true", help="list the cameras and exit")
args = parser.parse_args()

if args.list:
    by_id = Path("/dev/v4l/by-id")
    for p in sorted(by_id.glob("*-index0")) if by_id.exists() else []:
        print(f"{p}  ->  {p.resolve()}")
    raise SystemExit

cap = cv2.VideoCapture(int(args.cam) if args.cam.isdigit() else args.cam, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)
ok, frame = cap.read()
if not ok:
    raise SystemExit(
        f"Cannot read {args.cam}. Is it plugged in (--list)? Is another program using it "
        "(teleop, lerobot-record, ffplay)?"
    )

n, t0 = 0, time.perf_counter()
while time.perf_counter() - t0 < 2:
    ok, frame = cap.read()
    n += ok
brightness = frame.mean()
print(f"camera  : {args.cam}")
print(f"image   : {frame.shape[1]}x{frame.shape[0]}, {n / 2:.1f} fps measured (target {FPS})")
print(f"bright. : {brightness:.0f}/255" + ("  -> very dark: privacy shutter closed?" if brightness < 20 else ""))

overlay = None
if args.overlay:
    overlay = cv2.resize(cv2.imread(args.overlay), (WIDTH, HEIGHT))

viewer = subprocess.Popen(
    [
        "ffplay", "-loglevel", "error", "-window_title", "top camera",
        "-f", "rawvideo", "-pixel_format", "bgr24", "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", str(FPS), "-fflags", "nobuffer", "-flags", "low_delay", "-",
    ],
    stdin=subprocess.PIPE,
)
print("Live view open. Ctrl+C to stop.")
try:
    while viewer.poll() is None:
        ok, frame = cap.read()
        if not ok:
            continue
        shown = frame if overlay is None else cv2.addWeighted(frame, 1 - args.alpha, overlay, args.alpha, 0)
        if args.grid:
            shown = shown.copy()
            for i in (1, 2):
                cv2.line(shown, (WIDTH * i // 3, 0), (WIDTH * i // 3, HEIGHT), (0, 255, 255), 1)
                cv2.line(shown, (0, HEIGHT * i // 3), (WIDTH, HEIGHT * i // 3), (0, 255, 255), 1)
        try:
            viewer.stdin.write(np.ascontiguousarray(shown).tobytes())
        except BrokenPipeError:
            break
except KeyboardInterrupt:
    pass
finally:
    if args.save:
        cv2.imwrite(args.save, frame)
        print("Saved", args.save)
    cap.release()
    viewer.terminate()

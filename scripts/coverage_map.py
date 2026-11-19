"""Map where the object and the tray start in every episode of a dataset.

Detects the orange object and the dark tray in the first frame of each episode
(simple colour thresholds) and draws their positions on one image, so gaps in the
coverage of the workspace are easy to spot.

    conda activate lerobot
    python ~/SO-101/scripts/coverage_map.py                       # default dataset
    python ~/SO-101/scripts/coverage_map.py --root ~/SO-101/datasets/other --out map.png
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset

parser = argparse.ArgumentParser()
parser.add_argument("--root", default=str(Path.home() / "SO-101/datasets/so101_pick_place"))
parser.add_argument("--out", default=str(Path.home() / "SO-101/coverage_map.png"))
args = parser.parse_args()


def blob(mask: np.ndarray, min_area: int) -> tuple[tuple[int, int], np.ndarray] | None:
    """Centre and contour of the largest blob in a binary mask."""
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > min_area]
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    m = cv2.moments(c)
    return (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])), c


ds = LeRobotDataset(Path(args.root).name, root=args.root)
starts = ds.meta.episodes["dataset_from_index"]

canvas = None
for ep in range(ds.num_episodes):
    rgb = (ds[int(starts[ep])]["observation.images.top"].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    rgb = np.ascontiguousarray(rgb)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    if canvas is None:
        canvas = (rgb * 0.5).astype(np.uint8)  # dimmed first frame as background

    obj = blob(cv2.inRange(hsv, (5, 120, 120), (25, 255, 255)), 300)  # orange
    tray = blob(cv2.inRange(hsv, (0, 0, 20), (180, 120, 110)), 3000)  # dark brown/grey

    if tray:
        cv2.drawContours(canvas, [tray[1]], -1, (90, 140, 255), 1)
        cv2.circle(canvas, tray[0], 5, (90, 140, 255), -1)
    if obj:
        cv2.circle(canvas, obj[0], 5, (255, 170, 0), -1)
        cv2.putText(canvas, str(ep), (obj[0][0] + 6, obj[0][1] - 6), 0, 0.4, (255, 170, 0), 1)
    status = f"object {'ok' if obj else 'NOT FOUND'}, tray {'ok' if tray else 'NOT FOUND'}"
    print(f"episode {ep:3d}: {status}")

cv2.putText(canvas, "orange dots = object start   blue = tray start", (10, 470), 0, 0.5, (255, 255, 255), 1)
cv2.imwrite(args.out, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))
print(f"{ds.num_episodes} episodes -> {args.out}")

"""Health check of the pick-and-place dataset, episode by episode.

For every episode:
  - data: length, missing values, gripper opening
  - first frame: object (orange) and tray (dark) found? touching the image border (partly out of view)?
  - last frame: is the object inside the tray?
and a contact sheet (first | last frame of every episode) to eyeball the flagged ones.

    conda activate lerobot
    python ~/SO-101/scripts/dataset_health.py
    python ~/SO-101/scripts/dataset_health.py --root ~/SO-101/datasets/other
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

from lerobot.datasets.lerobot_dataset import LeRobotDataset

parser = argparse.ArgumentParser()
parser.add_argument("--root", default=str(Path.home() / "SO-101/datasets/so101_pick_place_cube"))
parser.add_argument("--out", default=str(Path.home() / "SO-101/health"))
args = parser.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)

BORDER = 4  # px: a blob this close to the edge is (partly) out of view


def frame(ds: LeRobotDataset, i: int) -> np.ndarray:
    return np.ascontiguousarray((ds[i]["observation.images.top"].permute(1, 2, 0).numpy() * 255).astype(np.uint8))


def blob(mask: np.ndarray, min_area: int) -> tuple[int, int, int, int] | None:
    """Bounding box (x, y, w, h) of the largest blob, or None."""
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > min_area]
    return cv2.boundingRect(max(contours, key=cv2.contourArea)) if contours else None


def detect(rgb: np.ndarray) -> tuple[tuple | None, tuple | None]:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    obj = blob(cv2.inRange(hsv, (5, 120, 120), (25, 255, 255)), 300)
    tray = blob(cv2.inRange(hsv, (0, 0, 20), (180, 120, 110)), 3000)
    return obj, tray


def at_border(box: tuple, h: int, w: int) -> bool:
    x, y, bw, bh = box
    return x <= BORDER or y <= BORDER or x + bw >= w - BORDER or y + bh >= h - BORDER


ds = LeRobotDataset(Path(args.root).name, root=args.root)
ep = ds.meta.episodes
actions = np.stack(ds.hf_dataset["action"])
print(f"{ds.num_episodes} episodes, {ds.num_frames} frames ({ds.num_frames / ds.fps / 60:.1f} min)\n")

tiles, flagged = [], []
for e in range(ds.num_episodes):
    a, b = int(ep["dataset_from_index"][e]), int(ep["dataset_to_index"][e])
    first, last = frame(ds, a), frame(ds, b - 1)
    h, w = first.shape[:2]
    obj0, tray0 = detect(first)
    obj1, tray1 = detect(last)

    issues = []
    if np.isnan(actions[a:b]).any():
        issues.append("NaN in actions")
    if b - a < 5 * ds.fps:
        issues.append(f"very short ({(b - a) / ds.fps:.1f}s)")
    if obj0 is None:
        issues.append("start: object not visible")
    elif at_border(obj0, h, w):
        issues.append("start: object at image edge")
    if tray0 is None:
        issues.append("start: tray not visible")
    elif at_border(tray0, h, w):
        issues.append("start: tray at image edge")
    if obj0 and tray0:
        ox, oy, ow, oh = obj0
        tx, ty, tw, th = tray0
        if tx <= ox + ow / 2 <= tx + tw and ty <= oy + oh / 2 <= ty + th:
            issues.append("start: object already in tray")
    if obj1 and tray1:
        ox, oy, ow, oh = obj1
        tx, ty, tw, th = tray1
        if not (tx <= ox + ow / 2 <= tx + tw and ty <= oy + oh / 2 <= ty + th):
            issues.append("end: object NOT in tray")
    elif obj1 is None:
        issues.append("end: object not visible")

    grip = actions[a:b, 5].max()
    print(f"ep {e:3d}  {(b - a) / ds.fps:4.1f}s  gripper max {grip:5.1f}%  " + ("; ".join(issues) if issues else "ok"))
    if issues:
        flagged.append(e)

    pair = []
    for img, (o, t) in ((first, (obj0, tray0)), (last, (obj1, tray1))):
        img = img.copy()
        for box, col in ((o, (255, 170, 0)), (t, (90, 140, 255))):
            if box:
                x, y, bw, bh = box
                cv2.rectangle(img, (x, y), (x + bw, y + bh), col, 2)
        pair.append(cv2.resize(img, (240, 180)))
    tile = np.hstack(pair)
    colour = (255, 60, 60) if issues else (60, 220, 60)
    cv2.rectangle(tile, (0, 0), (tile.shape[1] - 1, tile.shape[0] - 1), colour, 3)
    cv2.putText(tile, f"ep {e}", (6, 18), 0, 0.55, colour, 2)
    tiles.append(tile)

# contact sheets: 3 episodes per row, 8 rows per sheet
blank = np.zeros_like(tiles[0])
for s in range(0, len(tiles), 24):
    chunk = tiles[s : s + 24] + [blank] * (-len(tiles[s : s + 24]) % 3)
    sheet = np.vstack([np.hstack(chunk[i : i + 3]) for i in range(0, len(chunk), 3)])
    path = out / f"sheet_{s // 24}.jpg"
    cv2.imwrite(str(path), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
    print("contact sheet:", path)

print(f"\nflagged ({len(flagged)}): {flagged}")
print("Detections are colour-based: check the flagged episodes on the contact sheets before deleting anything.")

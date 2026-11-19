"""Check that this machine can train on the SO-101 dataset.

    conda activate lerobot
    python ~/SO-101/a6000/check_env.py
"""

import os
import subprocess
import sys
from pathlib import Path

EXPECTED_COMMIT = "87db15c8"
DATASET = Path.home() / "SO-101/datasets" / os.environ.get("DATASET", "so101_pick_place_clean")

ok = True


def report(name: str, good: bool, detail: str) -> None:
    global ok
    ok &= good
    print(f"[{'OK' if good else 'FAIL'}] {name}: {detail}")


import torch  # noqa: E402

report("python", sys.version_info[:2] == (3, 12), sys.version.split()[0])
report(
    "CUDA",
    torch.cuda.is_available(),
    torch.cuda.get_device_name(0) if torch.cuda.is_available() else f"not available (torch {torch.__version__})",
)

import lerobot  # noqa: E402

repo = Path(lerobot.__file__).resolve().parents[2]
commit = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%h"], capture_output=True, text=True).stdout.strip()
report("lerobot commit", commit.startswith(EXPECTED_COMMIT), f"{commit or 'unknown'} (expected {EXPECTED_COMMIT})")

try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    ds = LeRobotDataset(f"local/{DATASET.name}", root=DATASET)
    frame = ds[len(ds) - 1]["observation.images.top"]
    report("dataset", True, f"{ds.num_episodes} episodes, {ds.num_frames} frames, last frame decodes {tuple(frame.shape)}")
except Exception as e:  # noqa: BLE001 - report any loading/decoding problem
    report("dataset", False, f"{type(e).__name__}: {e}")

print("\nReady to train." if ok else "\nFix the FAIL lines first (see SETUP_A6000.md).")

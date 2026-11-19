# A6000 — setup & training

Training machine for the SO-101 pick-and-place ACT policy. The laptop records the data and runs the
trained policy; this machine only trains. No robot, camera or Feetech drivers needed here.

## What the A6000 needs

| Item | Why | Check |
|---|---|---|
| Linux + NVIDIA driver | CUDA training | `nvidia-smi` shows the RTX A6000 |
| Miniforge (conda) | same env manager as the laptop | `conda --version` |
| LeRobot **commit `87db15c8`** (v0.6.2) | dataset / model format must match the laptop | `git -C ~/lerobot log -1 --format=%h` |
| Python 3.12 + PyTorch with CUDA | training | `check_env.py` |
| `ffmpeg` from conda-forge | the dataset videos are **AV1**; TorchCodec needs ffmpeg to decode them | `check_env.py` |
| Internet (first run only) | ACT downloads ImageNet ResNet-18 weights from torchvision | — |
| Disk: ~5 GB free | env + dataset (~0.5 GB for 100 episodes) + checkpoints (~0.6 GB each) | `df -h ~` |

Laptop reference versions: python 3.12.14 · torch 2.11.0 · torchvision 0.26.0 · torchcodec 0.11.1 · av 15.1.0 · datasets 4.8.5 · lerobot 0.6.2.

## 1. Install (once)

**Easiest:** `bash ~/SO-101/a6000/install_a6000.sh` does all of this (env, LeRobot in `~/SO-101/lerobot`, ResNet weights, check). Manual steps below.

```bash
# Miniforge, if conda is not installed
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh        # then reopen the terminal

conda create -y -n lerobot python=3.12
conda activate lerobot
conda install -y ffmpeg -c conda-forge

git clone https://github.com/huggingface/lerobot.git ~/lerobot
cd ~/lerobot && git checkout 87db15c8
pip install -e ".[training]"
```

`pip install -e ".[training]"` installs a CUDA build of PyTorch by default. If `check_env.py` says CUDA is not
available, the driver is probably older than the CUDA version of that PyTorch build: install a matching
build from https://pytorch.org (e.g. `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126`).

## 2. Receive the dataset

From the laptop, `send_to_a6000.sh` copies everything into `~/SO-101/` here:

```
~/SO-101/datasets/so101_pick_place_clean/   the dataset (default in the scripts)
~/SO-101/a6000/                       this folder (setup notes + scripts)
```

## 3. Check the environment

```bash
conda activate lerobot
python ~/SO-101/a6000/check_env.py
```

It checks the GPU, the LeRobot commit, and that the dataset loads and its AV1 video decodes.

## 4. Train

```bash
conda activate lerobot
bash ~/SO-101/a6000/train_act.sh                    # defaults below
STEPS=30000 bash ~/SO-101/a6000/train_act.sh        # override any variable
```

Defaults: batch 32, 50 000 steps, checkpoint every 10 000 steps, image augmentation on
(brightness/contrast/saturation/hue/sharpness + small rotations/shifts → robustness to the demo venue).

Rough sizing (≈ 5–10+ epochs is the usual range for ACT):

| Episodes | Frames | Steps / epoch (batch 32) | 50k steps = |
|---:|---:|---:|---:|
| 45 | ~40 000 | ~1 250 | ~40 epochs |
| 100 | ~85 000 | ~2 650 | ~19 epochs |

Run it inside `tmux` so it survives a closed SSH session:

```bash
tmux new -s train        # detach: Ctrl+B then D · reattach: tmux attach -t train
```

Output: `~/SO-101/outputs/<run name>/checkpoints/<step>/pretrained_model/` (+ `last/` → latest).
Watch the `loss` in the log: it should drop quickly, then flatten.

## 5. Send the model back to the laptop

Only the `pretrained_model` folder is needed for inference (on the laptop):

```bash
rsync -avP <a6000-user>@<a6000-ip>:~/SO-101/outputs/<run name>/checkpoints/last/pretrained_model/ \
  ~/SO-101/models/<run name>/
```

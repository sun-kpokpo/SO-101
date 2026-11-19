#!/usr/bin/env bash
# One-time setup of a Linux laptop to teleoperate the SO-101 (no training, no camera).
# Needs internet. Run it BEFORE the showcase day:
#   bash install.sh
set -euo pipefail

KIT=$(cd "$(dirname "$0")" && pwd)
ENV=lerobot-demo
LEROBOT_DIR=$HOME/lerobot-demo-src
COMMIT=87db15c8

# 1. conda (Miniforge)
if ! command -v conda >/dev/null && [ ! -x "$HOME/miniforge3/bin/conda" ]; then
  echo ">>> Installing Miniforge"
  wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" -O /tmp/miniforge.sh
  bash /tmp/miniforge.sh -b -p "$HOME/miniforge3"
fi
CONDA_BASE=$( (command -v conda >/dev/null && conda info --base) || echo "$HOME/miniforge3")
# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 2. Python environment
if ! conda env list | grep -q "^$ENV "; then
  echo ">>> Creating conda env $ENV"
  conda create -y -n "$ENV" python=3.12
fi
conda activate "$ENV"

# 3. LeRobot, same version as the laptop the arms were calibrated with
if [ ! -d "$LEROBOT_DIR/.git" ]; then
  echo ">>> Downloading LeRobot"
  git clone https://github.com/huggingface/lerobot.git "$LEROBOT_DIR"
fi
git -C "$LEROBOT_DIR" fetch -q origin
git -C "$LEROBOT_DIR" checkout -q "$COMMIT"
echo ">>> Installing LeRobot + Feetech motor drivers (a few minutes)"
pip install -q -e "$LEROBOT_DIR[feetech]"

# 4. Permission to use the USB serial ports
if ! id -nG | grep -qw dialout; then
  echo ">>> Adding $USER to the 'dialout' group (asks for your password)"
  sudo usermod -aG dialout "$USER"
  NEED_RELOGIN=1
fi

chmod +x "$KIT/start_teleop.sh"
echo
echo "Installation done."
if [ "${NEED_RELOGIN:-0}" = 1 ]; then
  if grep -qi microsoft /proc/version; then
    echo "IMPORTANT (WSL): in Windows PowerShell run  wsl --shutdown  then reopen WSL, so the USB permission applies."
  else
    echo "IMPORTANT: log out and log back in (or reboot) once, so the USB permission applies."
  fi
fi
echo "Then plug the arms and run:  bash $KIT/start_teleop.sh --check"

#!/usr/bin/env bash
# One-shot setup of the A6000 for training (safe to run again: it skips what is already done).
#   bash ~/SO-101/a6000/install_a6000.sh
# Creates the conda env "lerobot" (python 3.12 + ffmpeg), installs LeRobot at the laptop's commit
# into ~/SO-101/lerobot, pre-downloads the ResNet-18 weights, then runs check_env.py.
set -euo pipefail

ENV_NAME=${ENV_NAME:-lerobot}
COMMIT=87db15c8
SRC=$HOME/SO-101/lerobot
MARKER=.so101_setup   # marks an env created by this script

step() { echo; echo "=== $* ==="; }

step "1/5 Find conda"
if ! command -v conda >/dev/null; then
  for base in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" /opt/conda; do
    [[ -x "$base/bin/conda" ]] && export PATH="$base/bin:$PATH" && break
  done
fi
command -v conda >/dev/null || { echo "conda not found. Install Miniforge first (see SETUP_A6000.md)."; exit 1; }
eval "$(conda shell.bash hook)"
echo "conda $(conda --version | cut -d' ' -f2) at $(conda info --base)"

step "2/5 Conda env '$ENV_NAME' (python 3.12 + ffmpeg)"
ENV_PREFIX=$(conda env list | awk -v n="$ENV_NAME" '$1 == n {print $NF}')
if [[ -z "$ENV_PREFIX" ]]; then
  conda create -y -n "$ENV_NAME" -c conda-forge --override-channels python=3.12 pip ffmpeg
  ENV_PREFIX=$(conda env list | awk -v n="$ENV_NAME" '$1 == n {print $NF}')
  touch "$ENV_PREFIX/$MARKER"
elif [[ ! -f "$ENV_PREFIX/$MARKER" ]]; then
  echo "An env named '$ENV_NAME' already exists and was not made by this script (someone else's?)."
  echo "Not touching it. Rerun with another name:  ENV_NAME=so101 bash $0"
  exit 1
else
  echo "already exists, reusing it"
fi
conda activate "$ENV_NAME"
[[ -x "$CONDA_PREFIX/bin/pip" ]] || conda install -y -c conda-forge --override-channels pip
echo "$(python --version), $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"

step "3/5 LeRobot source at $COMMIT -> $SRC"
[[ -d "$SRC/.git" ]] || git clone https://github.com/huggingface/lerobot.git "$SRC"
git -C "$SRC" fetch --quiet origin
git -C "$SRC" checkout --quiet "$COMMIT"
echo "at $(git -C "$SRC" log -1 --format='%h %s')"

step "4/5 pip install LeRobot (several minutes the first time)"
python -m pip --version && python -m pip install -e "$SRC[training]"

step "5/5 Pre-download ResNet-18 weights (used by ACT)"
python -c "import torchvision; torchvision.models.resnet18(weights='IMAGENET1K_V1'); print('ok')"

step "Environment check"
python "$(dirname "$0")/check_env.py"

command -v tmux >/dev/null || echo -e "\nNote: tmux is not installed (sudo apt install tmux). Training still works without it."
echo -e "\nNext:  conda activate $ENV_NAME && bash ~/SO-101/a6000/train_act.sh"

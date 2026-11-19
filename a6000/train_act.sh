#!/usr/bin/env bash
# Train ACT on the SO-101 pick-and-place dataset (run on the A6000).
# Override any variable from the command line, e.g.:  STEPS=30000 BATCH=16 bash train_act.sh
set -euo pipefail

DATASET=${DATASET:-$HOME/SO-101/datasets/so101_pick_place_clean}
STEPS=${STEPS:-50000}
BATCH=${BATCH:-32}
SAVE_FREQ=${SAVE_FREQ:-10000}
WORKERS=${WORKERS:-8}
RUN=${RUN:-act_pick_place_$(date +%Y%m%d_%H%M)}
OUT=$HOME/SO-101/outputs/$RUN

mkdir -p "$HOME/SO-101/outputs"
echo "dataset : $DATASET"
echo "run     : $RUN -> $OUT"
echo "steps   : $STEPS (batch $BATCH, checkpoint every $SAVE_FREQ)"

lerobot-train \
  --dataset.repo_id="local/$(basename "$DATASET")" \
  --dataset.root="$DATASET" \
  --dataset.image_transforms.enable=true \
  --policy.type=act \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --batch_size="$BATCH" \
  --steps="$STEPS" \
  --save_freq="$SAVE_FREQ" \
  --num_workers="$WORKERS" \
  --output_dir="$OUT" \
  --job_name="$RUN" \
  2>&1 | tee "$HOME/SO-101/outputs/$RUN.log"

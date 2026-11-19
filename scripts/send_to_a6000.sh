#!/usr/bin/env bash
# Copy the dataset + the A6000 setup folder from this laptop to the A6000.
#   bash ~/SO-101/scripts/send_to_a6000.sh <user>@<a6000-ip>
# Without network: bash send_to_a6000.sh --tar  -> creates ~/SO-101/so101_transfer.tar for a USB drive
#   (on the A6000: tar -xf so101_transfer.tar -C ~)
set -euo pipefail

DATASET=${DATASET:-so101_pick_place}   # folder name in ~/SO-101/datasets/, e.g. DATASET=so101_pick_place_clean
FILES=(SO-101/datasets/$DATASET SO-101/a6000)

if [[ "${1:-}" == "--tar" ]]; then
  tar -cf "$HOME/SO-101/so101_transfer.tar" -C "$HOME" "${FILES[@]}"
  ls -lh "$HOME/SO-101/so101_transfer.tar"
  exit 0
fi

DEST=${1:?usage: send_to_a6000.sh <user>@<a6000-ip>   (or --tar)}
ssh "$DEST" "mkdir -p ~/SO-101/datasets"
rsync -avP "$HOME/SO-101/datasets/$DATASET" "$DEST:~/SO-101/datasets/"
rsync -avP "$HOME/SO-101/a6000" "$DEST:~/SO-101/"
echo "Done. On the A6000: conda activate lerobot && python ~/SO-101/a6000/check_env.py"

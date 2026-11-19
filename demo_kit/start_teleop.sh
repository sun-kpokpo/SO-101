#!/usr/bin/env bash
# Start SO-101 teleoperation (leader arm drives the follower arm).
#   bash start_teleop.sh           start teleop (restart prompt after a crash)
#   bash start_teleop.sh --check   only check that both arms are connected and answer
set -uo pipefail

KIT=$(cd "$(dirname "$0")" && pwd)
export FOLLOWER_PORT=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B048489-if00
export LEADER_PORT=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A4B047977-if00

CONDA_BASE=$( (command -v conda >/dev/null && conda info --base) || echo "$HOME/miniforge3")
# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate lerobot-demo

ports_ok() {
  local ok=0
  [ -e "$FOLLOWER_PORT" ] || { echo "FOLLOWER board not detected: check its USB cable (board 5A4B048489)."; ok=1; }
  [ -e "$LEADER_PORT" ]   || { echo "LEADER board not detected: check its USB cable (board 5A4B047977)."; ok=1; }
  return $ok
}

if [ "${1:-}" = "--check" ]; then
  ports_ok || exit 1
  python "$KIT/check_arms.py"
  exit $?
fi

while true; do
  if ports_ok; then
    echo
    echo "Starting teleop. Put BOTH arms in the same (rest) pose first. Stop with Ctrl+C."
    lerobot-teleoperate \
      --robot.type=so101_follower --robot.port="$FOLLOWER_PORT" --robot.id=my_follower_arm \
      --robot.calibration_dir="$KIT/calibration" \
      --teleop.type=so101_leader --teleop.port="$LEADER_PORT" --teleop.id=my_leader_arm \
      --teleop.calibration_dir="$KIT/calibration" \
      --robot.max_relative_target=8 \
      --fps=30
    code=$?
    if [ $code -eq 0 ] || [ $code -eq 130 ]; then echo "Stopped."; exit 0; fi   # normal stop / Ctrl+C
    echo
    echo "Teleop stopped with an error (often: arm moved too fast -> power dip)."
  fi
  echo "Put both arms in the rest pose, check cables and power, then press Enter to restart (Ctrl+C to quit)."
  read -r || exit 0
done

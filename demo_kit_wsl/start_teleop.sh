#!/usr/bin/env bash
# Start SO-101 teleoperation (leader arm drives the follower arm).
#   bash start_teleop.sh           start teleop (restart prompt after a crash)
#   bash start_teleop.sh --check   only check that both arms are connected and answer
set -uo pipefail

KIT=$(cd "$(dirname "$0")" && pwd)
FOLLOWER_SERIAL=5A4B048489
LEADER_SERIAL=5A4B047977

CONDA_BASE=$( (command -v conda >/dev/null && conda info --base) || echo "$HOME/miniforge3")
# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate lerobot-demo

# Port of the board with this USB serial number. Uses /dev/serial/by-id when udev made it
# (normal Linux), otherwise reads the serial from sysfs (WSL without udev).
find_port() {
  local link=/dev/serial/by-id/usb-1a86_USB_Single_Serial_$1-if00 tty
  [ -e "$link" ] && { echo "$link"; return; }
  for tty in /sys/class/tty/ttyACM*; do
    [ -e "$tty" ] || continue
    [ "$(cat "$tty/device/../serial" 2>/dev/null)" = "$1" ] && { echo "/dev/$(basename "$tty")"; return; }
  done
}

ports_ok() {
  local ok=0
  FOLLOWER_PORT=$(find_port $FOLLOWER_SERIAL)
  LEADER_PORT=$(find_port $LEADER_SERIAL)
  [ -n "$FOLLOWER_PORT" ] || { echo "FOLLOWER board not detected (board $FOLLOWER_SERIAL): check its USB cable; on WSL run attach_arms.ps1 in Windows."; ok=1; }
  [ -n "$LEADER_PORT" ]   || { echo "LEADER board not detected (board $LEADER_SERIAL): check its USB cable; on WSL run attach_arms.ps1 in Windows."; ok=1; }
  export FOLLOWER_PORT LEADER_PORT
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

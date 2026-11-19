# SO-101 teleoperation — operator guide (Linux laptop)

You move the **leader** arm (the one with the handle) by hand; the **follower** arm copies it.

## Before the event (once, with internet)

1. Copy this `demo_kit` folder to the laptop, e.g. into your home folder (`~/demo_kit`).
2. Open a terminal and run:
   ```bash
   bash ~/demo_kit/install.sh
   ```
   It takes a few minutes. If it says so, **log out and back in** (or reboot) once.
3. Do a full test with the arms (steps below) — don't discover problems on the day.

## On the day

### 1. Connect

| Arm | Controller board label / serial | Power |
|---|---|---|
| Follower | `5A4B048489` | its own 5 V supply |
| Leader | `5A4B047977` | its own 5 V supply |

- Each board: power supply **+ to +, − to −** (reversed = nothing lights up), then USB to the laptop.
- The motor LEDs should light up red along the whole arm.
- Never use board `5A4B047947` (faulty).

### 2. Check

```bash
bash ~/demo_kit/start_teleop.sh --check
```

Expect `all 6 motors answer` for both arms and **READY**. Nothing moves during the check.

### 3. Start

1. Put **both arms in the same pose** — the folded rest pose is easiest. (The follower jumps to the leader's pose at start.)
2. Run:
   ```bash
   bash ~/demo_kit/start_teleop.sh
   ```
3. Move the leader **calmly and smoothly**. Fast, jerky moves can make the follower's power supply dip and stop the program.

### 4. Stop

**Ctrl+C** in the terminal. The follower's motors relax: **hold it or put it in the rest pose first**, it drops if it's raised.

## If something goes wrong

| What you see | What to do |
|---|---|
| Program stops with `There is no status packet` | Power dip (moved too fast). Put both arms in rest pose, press **Enter** to restart. |
| `board not detected` | Re-plug that board's USB cable; try another USB port. |
| `MISSING motors: [...]` in the check | That arm's power supply is off/loose, or a 3-pin cable between two motors came out (motors after the break have no LED). Reseat it. |
| Motor LEDs **blinking** | Overload or wrong power supply. Unplug power, wait 10 s, re-plug. |
| `Permission denied` on `/dev/...` | You didn't log out/in after the install. Do it. |
| Follower wrist spins a full turn | Restart with both arms in the same pose. |
| A program seems stuck / port busy | Close all terminals, then `pkill -INT -f lerobot-`, and start again. Never use Ctrl+**Z** (it pauses the program and keeps the arms locked). |

Do **not** run `lerobot-calibrate` — the calibration is already in the `calibration/` folder.

# SO-101 teleoperation — operator guide (Windows laptop with WSL)

You move the **leader** arm (the one with the handle) by hand; the **follower** arm copies it.

## Before the event (once, with internet)

This laptop runs the arms from **WSL** (Ubuntu inside Windows). WSL can't see USB devices on its own:
Windows forwards them with **usbipd**.

1. **Windows, PowerShell as Administrator** — install usbipd once, then close PowerShell:
   ```powershell
   winget install usbipd
   ```
2. **WSL** — copy this `demo_kit_wsl` folder to your WSL home folder (`~/demo_kit_wsl`), then:
   ```bash
   bash ~/demo_kit_wsl/install.sh
   ```
   It takes a few minutes. If it asks you to, run `wsl --shutdown` in PowerShell and reopen WSL.
3. Plug both arms, then **PowerShell as Administrator** (first time only, later a normal PowerShell is fine):
   ```powershell
   powershell -ExecutionPolicy Bypass -File \\wsl$\Ubuntu\home\<wsl-user>\demo_kit_wsl\attach_arms.ps1
   ```
   (or copy `attach_arms.ps1` to the Windows desktop and run it from there)
4. Do a full test with the arms (steps below) — don't discover problems on the day.

## On the day

### 1. Connect

| Arm | Controller board label / serial | Power |
|---|---|---|
| Follower | `5A4B048489` | its own 5 V supply |
| Leader | `5A4B047977` | its own 5 V supply |

- Each board: power supply **+ to +, − to −** (reversed = nothing lights up), then USB to the laptop.
- The motor LEDs should light up red along the whole arm.
- Never use board `5A4B047947` (faulty).
- **In Windows, run `attach_arms.ps1`** (PowerShell) to hand both boards to WSL. Redo it every time a board is
  re-plugged, or after Windows / WSL restarts.

### 2. Check

```bash
bash ~/demo_kit_wsl/start_teleop.sh --check
```

Expect `all 6 motors answer` for both arms and **READY**. Nothing moves during the check.

### 3. Start

1. Put **both arms in the same pose** — the folded rest pose is easiest. (The follower jumps to the leader's pose at start.)
2. Run:
   ```bash
   bash ~/demo_kit_wsl/start_teleop.sh
   ```
3. Move the leader **calmly and smoothly**. Fast, jerky moves can make the follower's power supply dip and stop the program.

### 4. Stop

**Ctrl+C** in the terminal. The follower's motors relax: **hold it or put it in the rest pose first**, it drops if it's raised.

## If something goes wrong

| What you see | What to do |
|---|---|
| Program stops with `There is no status packet` | Power dip (moved too fast). Put both arms in rest pose, press **Enter** to restart. |
| `board not detected` | Run `attach_arms.ps1` in Windows again. Still missing: re-plug that board's USB cable, try another USB port, run `attach_arms.ps1` again. |
| `attach_arms.ps1`: "No SO-101 board found" | The board isn't seen by Windows: check the USB cable. |
| `usbipd: error: ... not shared` | Run `attach_arms.ps1` once in PowerShell **as Administrator**. |
| `MISSING motors: [...]` in the check | That arm's power supply is off/loose, or a 3-pin cable between two motors came out (motors after the break have no LED). Reseat it. |
| Motor LEDs **blinking** | Overload or wrong power supply. Unplug power, wait 10 s, re-plug. |
| `Permission denied` on `/dev/...` | You didn't log out/in after the install. Do it. |
| Follower wrist spins a full turn | Restart with both arms in the same pose. |
| A program seems stuck / port busy | Close all terminals, then `pkill -INT -f lerobot-`, and start again. Never use Ctrl+**Z** (it pauses the program and keeps the arms locked). |

Do **not** run `lerobot-calibrate` — the calibration is already in the `calibration/` folder.

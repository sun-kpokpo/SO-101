# Forward the two SO-101 controller boards (USB serial 1a86:55d3) from Windows to WSL.
# Run in PowerShell. The FIRST time ever: run PowerShell "as Administrator" (needed to bind).
# Afterwards: run it again every time the boards are re-plugged or Windows/WSL restarted.
#   powershell -ExecutionPolicy Bypass -File attach_arms.ps1

if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
    Write-Host "usbipd is not installed. Run once (as Administrator):  winget install usbipd   then reopen PowerShell." -ForegroundColor Red
    exit 1
}

$boards = usbipd list | Select-String "1a86:55d3"
if (-not $boards) {
    Write-Host "No SO-101 board found. Check the USB cables (and that the boards are powered over USB)." -ForegroundColor Red
    exit 1
}

foreach ($line in $boards) {
    $busid = ($line.ToString().Trim() -split '\s+')[0]
    $text = $line.ToString()
    if ($text -notmatch "Shared|Attached") {
        Write-Host "Binding $busid (needs Administrator, first time only)"
        usbipd bind --busid $busid
    }
    if ($text -notmatch "Attached") {
        Write-Host "Attaching $busid to WSL"
        usbipd attach --wsl --busid $busid
    } else {
        Write-Host "$busid already attached to WSL"
    }
}
Write-Host "Done. In WSL run:  bash ~/demo_kit_wsl/start_teleop.sh --check" -ForegroundColor Green

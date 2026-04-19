# Install MX Master 4 haptic daemon on Windows.
# Registers a scheduled task that launches the daemon silently at every user logon.
#
# Usage (no admin required):
#   powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

$daemon  = Join-Path $PSScriptRoot "haptics_daemon_win.py"
if (-not (Test-Path $daemon)) { throw "Daemon script not found: $daemon" }

$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)
if (-not $pythonw) { throw "pythonw.exe not found on PATH. Install Python 3 and re-run." }
$pythonwPath = $pythonw.Source

# Ensure 'requests' is available
Write-Host "Checking Python dependencies..."
& $pythonwPath -c "import requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing 'requests'..."
    & (Get-Command python.exe).Source -m pip install requests | Out-Null
}

$taskName = "MXMaster4Haptics"
$action    = New-ScheduledTaskAction -Execute $pythonwPath -Argument "`"$daemon`""
$trigger   = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings  = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Days 3650) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "MX Master 4 haptic feedback daemon" `
    -Force | Out-Null

Start-ScheduledTask -TaskName $taskName

Write-Host ""
Write-Host "Done. Task '$taskName' runs at every logon and is running now."
Write-Host ""
Write-Host "Manage:"
Write-Host "  Stop:    Stop-ScheduledTask -TaskName $taskName"
Write-Host "  Start:   Start-ScheduledTask -TaskName $taskName"
Write-Host "  Remove:  Unregister-ScheduledTask -TaskName $taskName -Confirm:`$false"

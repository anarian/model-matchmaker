# Auto-Switch Model via Keyboard Automation (Windows)
# Uses Ctrl+/ to open Cursor's model dropdown, then arrow keys to navigate.
#
# Cursor's keyboard shortcut for model switching:
#   Ctrl+/ - loop between AI models (opens dropdown)
#   Arrow keys + Enter - navigate and select
#
# Uses WScript.Shell SendKeys to drive the Cursor window directly.
# No extra installs required; Cursor window must be in the foreground.
#
# Usage: powershell -File auto-switch-model.ps1 <model_name> [-Test]
# Example: powershell -File auto-switch-model.ps1 sonnet
# Test mode: powershell -File auto-switch-model.ps1 sonnet -Test

param(
    [Parameter(Mandatory=$true)][string]$Model,
    [switch]$Test
)

$hookDir   = Join-Path $env:USERPROFILE ".cursor\hooks"
$logFile   = Join-Path $hookDir "auto-switch-audit.log"
$circuitFile = Join-Path $hookDir ".auto-switch-circuit"
$lockFile  = Join-Path $hookDir ".auto-switch.lock"
$killSwitch = Join-Path $hookDir ".auto-switch-kill"
$enableFlag = Join-Path $hookDir ".auto-switch-enabled"
$modeFile  = Join-Path $hookDir ".cursor-mode"

New-Item -ItemType Directory -Force -Path $hookDir | Out-Null

function Write-Log([string]$msg) {
    $ts = (Get-Date -Format "o")
    Add-Content -Path $logFile -Value "[$ts] $msg"
}

# SECURITY: Emergency kill switch
if (Test-Path $killSwitch) {
    Write-Log "SECURITY: Kill switch activated"
    exit 0
}

# SECURITY: Check enable flag (skip in test mode)
if (-not $Test -and -not (Test-Path $enableFlag)) {
    exit 0
}

# SECURITY: Input validation - only allow whitelisted model names
if ($Model -notin @("haiku", "sonnet", "opus")) {
    Write-Log "SECURITY: Invalid model rejected: $Model"
    exit 1
}

# SECURITY: Execution lock - prevent simultaneous executions
if (Test-Path $lockFile) {
    $lockAge = ((Get-Date) - (Get-Item $lockFile).LastWriteTime).TotalSeconds
    if ($lockAge -lt 10) {
        Write-Log "SECURITY: Lock exists, switch in progress"
        exit 0
    } else {
        Remove-Item -Force $lockFile -ErrorAction SilentlyContinue
    }
}

New-Item -ItemType File -Force -Path $lockFile | Out-Null
try {

# SECURITY: Rate limiting - prevent rapid-fire switching
$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
if (Test-Path $circuitFile) {
    $lastSwitch = [long](Get-Content $circuitFile -Raw -ErrorAction SilentlyContinue)
    $timeDiff = $now - $lastSwitch
    if ($timeDiff -lt 5) {
        Write-Log "SECURITY: Rate limit - too soon since last switch (${timeDiff}s)"
        exit 0
    }
}
Set-Content -Path $circuitFile -Value $now

# Detect current Cursor mode (affects dropdown positions)
$cursorMode = "agent"
if (Test-Path $modeFile) {
    $cursorMode = (Get-Content $modeFile -Raw -ErrorAction SilentlyContinue).Trim()
    if (-not $cursorMode) { $cursorMode = "agent" }
}

Write-Log "SWITCH_ATTEMPT | Model: $Model | Mode: $cursorMode | PID: $PID | User: $env:USERNAME"

# Model dropdown positions
# Agent/Debug/Ask modes: Auto=0, MAX=1, Composer=2, GPT=3, Opus=4, Haiku=5, Sonnet=6
# Plan mode:            Auto=0, MAX=1, Composer=2, GPT=3, Opus=4, [Haiku grayed/skipped], Sonnet=5
#
# In Plan mode Haiku is grayed out; arrow-down skips it, shifting positions after it up by one.

if ($cursorMode -eq "plan") {
    switch ($Model) {
        "opus"   { $arrowPresses = 4 }
        "haiku"  {
            Write-Log "INFO | Haiku not available in Plan mode, switching to Sonnet"
            $Model = "sonnet"
            $arrowPresses = 5
        }
        "sonnet" { $arrowPresses = 5 }
    }
} else {
    switch ($Model) {
        "opus"   { $arrowPresses = 4 }
        "haiku"  { $arrowPresses = 5 }
        "sonnet" { $arrowPresses = 6 }
    }
}

# Bring Cursor to foreground and send keys
$wsh = New-Object -ComObject WScript.Shell

if (-not $wsh.AppActivate("Cursor")) {
    Write-Log "FAILED | Could not activate Cursor window"
    exit 1
}

Start-Sleep -Milliseconds 400

# Ctrl+/ opens the model dropdown
$wsh.SendKeys("^/")
Start-Sleep -Milliseconds 600

# Navigate to target model
for ($i = 0; $i -lt $arrowPresses; $i++) {
    $wsh.SendKeys("{DOWN}")
    Start-Sleep -Milliseconds 100
}

Start-Sleep -Milliseconds 200
$wsh.SendKeys("{ENTER}")

Write-Log "SUCCESS | Model: $Model"

} finally {
    Remove-Item -Force $lockFile -ErrorAction SilentlyContinue
}

# Launch Windows Terminal with split panes and virtual environment using current path
$scriptPath = (Get-Location).Path
$venvPath = Join-Path $scriptPath "env\Scripts\activate.ps1"

if (-not (Test-Path $venvPath)) {
    Write-Host "Error: Virtual environment not found at $venvPath"
    exit 1
}

wt.exe --size 210,30 --pos 0,150 -d $scriptPath powershell.exe -NoExit -Command ". '$venvPath'" `
    `; split-pane -V -d $scriptPath powershell.exe -NoExit -Command ". '$venvPath'"
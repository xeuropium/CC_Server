# Launch Windows Terminal with split panes and virtual environment using relative paths
$scriptPath = (Get-Location).Path
$venvPath = Join-Path $scriptPath "env\Scripts\activate.ps1"

# Check if virtual environment exists
if (-not (Test-Path $venvPath)) {
    Write-Host "Error: Virtual environment not found at $venvPath"
    exit 1
}

# Launch Windows Terminal with two split panes
wt.exe -d $scriptPath powershell.exe -NoExit -Command ". '$venvPath'" `
    `; split-pane -V -d $scriptPath powershell.exe -NoExit -Command ". '$venvPath' ; powershell.exe echo test"
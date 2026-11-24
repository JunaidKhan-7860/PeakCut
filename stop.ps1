$Host.UI.RawUI.WindowTitle = "Stopping PeakCut..."
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   STOPPING PEAKCUT SERVICES" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Stop PeakCut Python server
$pyProcesses = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*studio.server*" }
if ($pyProcesses) {
    foreach ($p in $pyProcesses) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] PeakCut Studio Server stopped." -ForegroundColor Green
} else {
    Write-Host "[INFO] PeakCut Studio Server was not running." -ForegroundColor White
}

# Stop PeakCut Autonomous Engine
$engineProcesses = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*autonomous_engine.py*" }
if ($engineProcesses) {
    foreach ($p in $engineProcesses) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] PeakCut Autonomous Engine stopped." -ForegroundColor Green
} else {
    Write-Host "[INFO] PeakCut Autonomous Engine was not running." -ForegroundColor White
}

# Stop Ollama if running
$ollamaProcesses = Get-Process -Name "*ollama*" -ErrorAction SilentlyContinue
if ($ollamaProcesses) {
    $ollamaProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Ollama Local AI stopped." -ForegroundColor Green
} else {
    Write-Host "[INFO] Ollama Local AI was not running." -ForegroundColor White
}

Write-Host ""
Write-Host "All PeakCut services stopped cleanly. RAM & GPU memory freed." -ForegroundColor Green
Start-Sleep -Seconds 2

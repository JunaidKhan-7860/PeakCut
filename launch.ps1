$Host.UI.RawUI.WindowTitle = "Starting AI Viral Clipper..."
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AI VIRAL CLIPPER STUDIO - STARTING SERVICES" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Ollama Local AI if not running
$ollamaOk = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 1 -ErrorAction Stop
    $ollamaOk = $true
} catch {}

if (-not $ollamaOk) {
    Write-Host "[1/3] Starting Local AI Engine (Ollama Llama 3.2)..." -ForegroundColor White
    $ollamaPath = "C:\Users\jarhj\AppData\Local\Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaPath) {
        Start-Process -FilePath $ollamaPath -ArgumentList "serve" -WindowStyle Hidden
    }
} else {
    Write-Host "[1/3] Local AI Engine is already running." -ForegroundColor Green
}

# 2. Start PeakCut Server if not running
$peakcutOk = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:8765/healthz" -TimeoutSec 1 -ErrorAction Stop
    if ($res.ok -eq $true) {
        $peakcutOk = $true
    }
} catch {}

if (-not $peakcutOk) {
    Write-Host "[2/3] Starting PeakCut Studio Server..." -ForegroundColor White
    Start-Process -FilePath "C:\peakcut\.venv\Scripts\python.exe" -ArgumentList "-m", "studio.server" -WorkingDirectory "C:\peakcut" -WindowStyle Hidden
} else {
    Write-Host "[2/3] PeakCut Studio Server is already running." -ForegroundColor Green
}

# 3. Wait for PeakCut Server to become ready
Write-Host "[3/3] Connecting to PeakCut Web Studio..." -ForegroundColor White
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8765/healthz" -TimeoutSec 1 -ErrorAction Stop
        if ($res.ok -eq $true) {
            $ready = $true
            break
        }
    } catch {}
}

if ($ready) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "   SUCCESS! PEAKCUT STUDIO IS RUNNING" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "   - Web Studio:          http://127.0.0.1:8765/app" -ForegroundColor Cyan
    Write-Host "   - Ready to Publish:    http://127.0.0.1:8765/staged" -ForegroundColor Cyan
    Write-Host "   - Free AI Model:       Llama 3.2 (RTX 3050 Accelerated)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Opening Web Studio in your browser..." -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8765/app"
    Start-Sleep -Seconds 2
} else {
    Write-Host ""
    Write-Host "[NOTICE] Opening browser now. If the page is still loading, refresh in a few seconds." -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8765/app"
    Start-Sleep -Seconds 2
}

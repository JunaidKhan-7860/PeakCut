$Host.UI.RawUI.WindowTitle = "Starting Khan Clipping AI Studio..."
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "   KHAN CLIPPING - NEON AI VIRAL STUDIO" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host ""

$workDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
$pyExe = if (Test-Path "$workDir\.venv\Scripts\python.exe") { "$workDir\.venv\Scripts\python.exe" }
         elseif (Test-Path "C:\peakcut\.venv\Scripts\python.exe") { "C:\peakcut\.venv\Scripts\python.exe" }
         else { "python" }

# 1. Start Ollama Local AI if not running
$ollamaOk = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 1 -ErrorAction Stop
    $ollamaOk = $true
} catch {}

if (-not $ollamaOk) {
    Write-Host "[1/4] Starting Local AI Engine (Ollama Llama 3.2)..." -ForegroundColor White
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaCmd) {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    } else {
        $localOllama = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
        if (Test-Path $localOllama) {
            Start-Process -FilePath $localOllama -ArgumentList "serve" -WindowStyle Hidden
        }
    }
} else {
    Write-Host "[1/4] Local AI Engine is already running." -ForegroundColor Green
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
    Write-Host "[2/4] Starting PeakCut Web Server (FastAPI)..." -ForegroundColor White
    Start-Process -FilePath $pyExe -ArgumentList "-m", "studio.server" -WorkingDirectory $workDir -WindowStyle Hidden
} else {
    Write-Host "[2/4] PeakCut Web Server is already running." -ForegroundColor Green
}

# 3. Start Autonomous Viral Engine if not running
$engineProcess = Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%autonomous_engine.py%'" -ErrorAction SilentlyContinue
if (-not $engineProcess) {
    Write-Host "[3/4] Starting 24/7 Autonomous Viral Engine..." -ForegroundColor White
    Start-Process -FilePath $pyExe -ArgumentList "autonomous_engine.py" -WorkingDirectory $workDir -WindowStyle Hidden
} else {
    Write-Host "[3/4] Autonomous Viral Engine is already running." -ForegroundColor Green
}

# 4. Wait for PeakCut Server to become ready
Write-Host "[4/4] Connecting to PeakCut Web Studio..." -ForegroundColor White
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
    Write-Host "   SUCCESS! KHAN CLIPPING STUDIO IS RUNNING" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "   - Live Dashboard:      http://127.0.0.1:8765/dashboard" -ForegroundColor Cyan
    Write-Host "   - Neon Studio Editor:  http://127.0.0.1:8765/app" -ForegroundColor Magenta
    Write-Host "   - Local AI Brain:      Llama 3.2 + Whisper + NVENC" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Opening Live Dashboard in your browser..." -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8765/dashboard"
    Start-Sleep -Seconds 2
} else {
    Write-Host ""
    Write-Host "[NOTICE] Opening browser now. If the page is still loading, refresh in a few seconds." -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8765/dashboard"
    Start-Sleep -Seconds 2
}

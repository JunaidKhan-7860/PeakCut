# PeakCut AI - Automated Antigravity One-Click Setup Script
$Host.UI.RawUI.WindowTitle = "PeakCut AI - Antigravity Setup"
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   PEAKCUT AI - ANTIGRAVITY ONE-CLICK SETUP" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$workDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
Set-Location $workDir

# 1. Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor White
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    Write-Host "[ERROR] Python 3.10+ is required. Please install Python from https://www.python.org/downloads/ and try again." -ForegroundColor Red
    pause
    exit 1
}
Write-Host "      Python found: $(python --version)" -ForegroundColor Green

# 2. Setup Virtual Environment
Write-Host "[2/5] Setting up Python virtual environment..." -ForegroundColor White
if (-not (Test-Path "$workDir\.venv")) {
    Write-Host "      Creating .venv in $workDir..." -ForegroundColor Gray
    python -m venv .venv
}
$pyExe = "$workDir\.venv\Scripts\python.exe"
$pipExe = "$workDir\.venv\Scripts\pip.exe"
Write-Host "      Virtual environment ready." -ForegroundColor Green

# 3. Install Dependencies
Write-Host "[3/5] Installing requirements (FastAPI, yt-dlp, Whisper, Pillow)..." -ForegroundColor White
& $pipExe install -r requirements.txt --quiet
Write-Host "      Dependencies installed." -ForegroundColor Green

# 4. Check Environment Config
Write-Host "[4/5] Checking configuration & Antigravity integration..." -ForegroundColor White
if (-not (Test-Path "$workDir\.env")) {
    if (Test-Path "$workDir\.env.example") {
        Copy-Item "$workDir\.env.example" "$workDir\.env"
        Write-Host "      Created .env from .env.example." -ForegroundColor Green
    }
} else {
    Write-Host "      Configuration .env found." -ForegroundColor Green
}

# Optional: Register global skill in Antigravity config directory if present
$targetSkillDirs = @(
    "$env:USERPROFILE\.gemini\config\skills\peakcut",
    "$env:USERPROFILE\.gemini\antigravity\skills\peakcut"
)
foreach ($targetDir in $targetSkillDirs) {
    $parentDir = Split-Path $targetDir
    if (Test-Path $parentDir) {
        try {
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
            }
            Copy-Item -Path "$workDir\.agents\skills\peakcut\*" -Destination $targetDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "      Linked PeakCut skill into Antigravity ($targetDir)!" -ForegroundColor Green
            break
        } catch {}
    }
}

# 5. Launch PeakCut Studio
Write-Host "[5/5] Launching PeakCut Studio..." -ForegroundColor White
powershell -ExecutionPolicy Bypass -File "$workDir\launch.ps1"

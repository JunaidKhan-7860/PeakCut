# PeakCut AI — Antigravity Agent Guidelines

Welcome to PeakCut AI! When working in this repository in Google Antigravity, follow these instructions to manage and operate the tool effortlessly for the user.

---

## 🚀 Quick Command Reference for Agents

Task | Preferred Command | Expected Output
:--- | :--- | :---
**Start All Services** | `.\start.bat` or `powershell -ExecutionPolicy Bypass -File .\launch.ps1` | Starts Ollama, FastAPI server on `:8765`, and autonomous engine daemon
**Start Server Only** | `& .\.venv\Scripts\python.exe -m studio.server` | Web server on `http://127.0.0.1:8765`
**Start Autonomous Engine** | `& .\.venv\Scripts\python.exe autonomous_engine.py` | 24/7 AI stream discovery & clipping daemon
**Stop All Services** | `.\stop.bat` or `powershell -ExecutionPolicy Bypass -File .\stop.ps1` | Stops server, engine, and local AI cleanly
**Check Health** | `Invoke-RestMethod http://127.0.0.1:8765/healthz` | `{"ok": true}`
**List Staged Clips** | `Invoke-RestMethod http://127.0.0.1:8765/api/staged_clips` | Array of staged clip packages
**Check Engine Status** | `Invoke-RestMethod http://127.0.0.1:8765/api/autonomous/status` | Engine state, active streams, and recent logs

---

## 🌐 Web Endpoints
* **Live Dashboard**: `http://127.0.0.1:8765/dashboard` — Obsidian slate dashboard with live terminal stream, ready clips, and metrics.
* **Pro Studio & Clip Editor**: `http://127.0.0.1:8765/app` — Full workstation with mobile phone mockup and 5-tab controls.
* **Staged Review**: `http://127.0.0.1:8765/staged`

---

## 🛡️ Important Safety & Operational Rules
1. **MANDATORY APPROVAL BEFORE SUBMISSION**: ALWAYS ask the user before submitting, posting, or publishing any clip to YouTube, TikTok, Instagram, or any external platform. NEVER auto-submit without the user's explicit, direct confirmation.
2. **Never commit secrets**: Keep `.env`, tokens, passwords, and private cookies strictly uncommitted. `.gitignore` is pre-configured.
3. **Safe Clipping Mode**: By default, `POSTING_ENABLED = False` in `autonomous_engine.py` and `POSTING_PAUSED = True` in `auto_poster.py`. Never change this without the user's explicit instruction to start uploading.
4. **Hardware Acceleration**: The engine automatically uses NVIDIA NVENC hardware encoding (1080x1920 60FPS) if available, falling back to CPU x264 seamlessly.
5. **Local AI Engine**: Runs on local Ollama `llama3.2:latest` at `http://127.0.0.1:11434`. Zero cloud token cost.

---

## 🛠️ First-Time Setup in Antigravity
If the user opens this repository for the first time on a new computer:
1. Ensure Python 3.10+ and FFmpeg (`winget install Gyan.FFmpeg`) are installed.
2. Set up virtualenv:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` if `.env` does not exist.
4. Launch with `powershell -ExecutionPolicy Bypass -File .\launch.ps1`!

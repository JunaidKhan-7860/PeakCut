---
name: peakcut
description: >-
  Autonomous AI Video Clipping Studio. Use this skill when the user asks to start, manage,
  clip videos, open the dashboard, inspect staged clips, or run PeakCut in Antigravity.
---

# PeakCut AI Studio Skill

This skill teaches Antigravity agents how to run, manage, and inspect the PeakCut AI Video Clipping Studio.

## When to Use This Skill
Activate this skill whenever the user asks to:
* "Start PeakCut", "launch PeakCut", or "run the clipping tool"
* "Open the dashboard", "show my clips", or "open the studio"
* "Clip this stream", "cut highlights", or "process a YouTube VOD"
* "Check engine status" or "view autonomous logs"
* "Stop PeakCut" or "free up GPU memory"

---

## 🚀 Execution Procedures

### 1. Launching PeakCut Studio
Run the universal launcher in PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\launch.ps1
```
Or start individual services:
* **Web Server**: `& .\.venv\Scripts\python.exe -m studio.server`
* **Autonomous Clipping Engine**: `& .\.venv\Scripts\python.exe autonomous_engine.py`

Once started, point the user to:
* **Live Dashboard**: [http://127.0.0.1:8765/dashboard](http://127.0.0.1:8765/dashboard)
* **Pro Studio Editor**: [http://127.0.0.1:8765/app](http://127.0.0.1:8765/app)

---

### 2. Inspecting Staged Clips
To query the AI-rendered clips:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/staged_clips"
```
Returns an array of staged packages containing:
* `title`: AI viral headline
* `video_url`: Local or Cloud CDN streaming link
* `thumb_url`: High-resolution poster
* `score`: Retention prediction score (e.g. 94)
* `target_creator`: Target channel or campaign name

---

### 3. Checking Autonomous Engine Status & Logs
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/autonomous/status"
```
Returns:
* `running`: Boolean
* `posting_frozen`: Boolean (`true` indicates Safe Clipping Mode)
* `recent_logs`: Real-time streaming log lines from `autonomous_engine.log`

---

### 4. Stopping Services
To terminate all background processes cleanly:
```powershell
powershell -ExecutionPolicy Bypass -File .\stop.ps1
```

---

## 🛡️ Operating Rules
* **Safe Clipping Guard**: Posting is frozen by default (`POSTING_ENABLED = False`). Clips are staged for review without auto-publishing to YouTube or Instagram.
* **Storage Protection**: PeakCut automatically offloads large video files to Cloud CDN to preserve PC hard drive space.

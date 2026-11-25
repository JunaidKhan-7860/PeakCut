---
name: khan-clipping
description: >-
  Khan Clipping Autonomous Neon AI Video Studio. Use this skill when the user asks to start,
  manage, clip videos, configure Hinglish Always-Fix words, check system readiness, open the
  dashboard, or run Khan Clipping / PeakCut in Antigravity.
---

# Khan Clipping AI Studio Skill

Khan Clipping combines **PeakCut's** 24/7 autonomous agency engine, Cloud CDN offloading, and 5-tab mobile studio with **NeonClipping's** Vice-City Neon Synthwave UI, Hinglish loanword engine, Always-Fix glossary, excitement lexicon, 13 caption styles, 5-star preference ranker, and watch-folder automation.

## Quick Commands
* **Start Everything**: `powershell -ExecutionPolicy Bypass -File .\launch.ps1`
* **Stop Services**: `powershell -ExecutionPolicy Bypass -File .\stop.ps1`
* **Live Dashboard**: [http://127.0.0.1:8765/dashboard](http://127.0.0.1:8765/dashboard)
* **Neon Studio Editor**: [http://127.0.0.1:8765/app](http://127.0.0.1:8765/app)
* **System Readiness**: `Invoke-RestMethod http://127.0.0.1:8765/api/readiness`
* **Staged Clips**: `Invoke-RestMethod http://127.0.0.1:8765/api/staged_clips`

## Mandatory Operating Rules
* **Mandatory User Approval Before Submission**: NEVER submit, publish, or upload any clip to YouTube, Instagram, or TikTok without presenting the clip to the user and asking for explicit approval first.
* **Safe Clipping Guard**: Posting is frozen by default (`POSTING_ENABLED = False`, `POSTING_PAUSED = True`).

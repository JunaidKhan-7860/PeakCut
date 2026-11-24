# PeakCut AI — Antigravity Agent Manual

A comprehensive guide for Google Antigravity agents, contributors, and AI coding assistants.

---

## 🤖 Running Inside Google Antigravity

If you are an Antigravity agent or developer working with this codebase:
* **1-Click Setup**: Run `powershell -ExecutionPolicy Bypass -File .\install_antigravity.ps1`
* **1-Click Launch**: Run `powershell -ExecutionPolicy Bypass -File .\launch.ps1` or double-click `start.bat`.
* **Live Dashboard**: Point the user to `http://127.0.0.1:8765/dashboard` (Obsidian slate theme with real-time metrics, live terminal logs, and campaign filters).
* **Studio Editor**: Point the user to `http://127.0.0.1:8765/app` (Spacious 1180px workstation with 9:16 smartphone mockup preview and 5-tab controls).
* **Antigravity Skill**: This repository includes a native Antigravity skill located at `.agents/skills/peakcut/SKILL.md` and project rules in `GEMINI.md`.
* **Clean Shutdown**: Run `powershell -ExecutionPolicy Bypass -File .\stop.ps1` or double-click `stop.bat`.

---

## 💻 Installing or Updating PeakCut

**Before installing, ask the person where to put it**, and suggest a short, permanent folder: `C:\peakcut` on
Windows, `~/peakcut` on a Mac or Linux. Do not just clone into the folder you happen to be running in: AI assistants
often run in a temporary, scratch or session workspace, which gets deleted, and whose path is long enough that
Windows cannot load the speech library (Windows can't open files whose full path is over 260 characters; the error
is "DLL load failed ... The filename or extension is too long").

**When updating**, look at where PeakCut is first. If its folder path is long (roughly over 100 characters) or inside
a temporary or assistant workspace, move it to `C:\peakcut` (or `~/peakcut`). Moving is safe when done like this: clone the latest version into the new folder, copy over `.env`, `storage.json` and the `data` folder if there is one, install the requirements, start it from the new folder, check the clips are there, and only then offer to delete the old folder.

---

## 🚀 Run and Test

- Run: `python -m studio.server` (settings from `.env`; see `.env.example`). Needs Python 3.10+ and `ffmpeg`.
- The English speech model (about 480 MB) downloads by itself on first start; `python -m studio.fetch_model` gets it ahead of time.
- Tests: `python tests/run.py`. It starts a throwaway copy on a spare port with an empty data folder. Run it before and after any change to `studio/`. No keys needed.

---

## 📁 Architecture Overview

| File / Folder | What it does |
|---|---|
| `studio/server.py` | FastAPI web routes, REST endpoints, and security/rate gates |
| `studio/render.py` | Cutting, 1080x1920 60FPS NVENC layouts, kinetic subtitles, Lanczos upscaling |
| `studio/facecam.py` | Dynamic facecam tracking, isolation, and split-screen composition |
| `studio/brain.py` | Llama 3.2 offline neural scoring, viral hook prompts, and caption polish |
| `studio/cloud_storage.py`| Cloud CDN offloading and zero-PC disk storage cleaner |
| `studio/roles.py` | 12-Director autonomous agency syndicate structure |
| `studio/transcribe.py` | Whisper word-by-word timestamped speech-to-text |
| `studio/rights.py` | Editorial standards and license verification gate |
| `autonomous_engine.py` | 24/7 autonomous VOD discovery and clipping daemon |
| `web/dashboard.html` | Obsidian dark mode live control dashboard |
| `web/index.html` | Pro Studio editor with 9:16 vertical smartphone frame mockup |
| `.agents/skills/` | Native Google Antigravity skill definitions |
| `GEMINI.md` | Antigravity project rules and instructions |

---

## 🛡️ Security & Operational Standards

- **Safe Clipping Guard**: By default, `POSTING_ENABLED = False` in `autonomous_engine.py` and `POSTING_PAUSED = True` in `auto_poster.py`. Clips are generated and safely staged for human review.
- **Secrets Protection**: `.env`, tokens, passwords, and private cookies must NEVER be committed to version control.
- **Offline First**: All neural operations default to local Ollama Llama 3.2. Zero cloud token costs.

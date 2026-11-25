# Khan Clipping — Autonomous Neon AI Video Studio

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Modern%20Web-009688.svg)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Local%20AI-Llama%203.2-orange.svg)](https://ollama.com/)
[![Whisper ASR](https://img.shields.io/badge/Speech%20Recognition-Whisper-green.svg)](https://github.com/openai/whisper)
[![NVIDIA NVENC](https://img.shields.io/badge/Hardware%20Accel-1080x1920%2060FPS-76B900.svg)](https://developer.nvidia.com/video-encode-decode-gpu-support-matrix)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **The Ultimate Combined AI Clipper**: Merges **PeakCut's 24/7 Autonomous Agency Syndicate, Cloud CDN Offloading, & Pro 5-Tab Studio** with **NeonClipping's Vice-City Synthwave Neon UI, Hinglish Loanwords, Always-Fix Dictionary, Excitement Lexicon, 13 Caption Styles, & 5-Star Preference Ranker.**

---

## 🌟 Overview

**Khan Clipping** turns uncut live streams and long YouTube/Twitch/Kick VODs into captioned, viral 9:16 vertical clips (1080x1920 60FPS) — 100% locally with **zero subscription fees** and **mandatory Safe Staging review** before anything ever posts.

---

## ⚡ Key Highlights

### 1. 🧠 Offline Local AI Brain (Llama 3.2 + Whisper)
* **Local Neural Scoring**: Evaluates audio transcripts offline using **Ollama Llama 3.2** to detect peak emotional climaxes (rages, clutches, shock moments, educational epiphanies).
* **High-Precision Speech Alignment**: Whisper speech-to-text generates word-by-word timestamped subtitles.
* **100% Free**: No OpenAI, Anthropic, or external API bills required.

### 2. 🎬 Modern Pro Studio & Live Dashboard
* **Interactive Dashboard (`/dashboard`)**: Deep slate dark mode with real-time clip metrics, live system terminal logs, and campaign filters.
* **Pro Clip Editor (`/app`)**: Spacious 1180px workstation featuring an authentic **9:16 mobile phone mockup frame** and 5-tab segmented controls:
  1. 🎯 **Hook & Style**: Viral headlines, 1-click presets, punch zoom (+15%), retention progress bars, and transcript editor.
  2. ⚡ **Flash-Forward Climax Teaser**: Plays the peak moment at 00:00 for ~2s with high-CTR teaser badges (`WAIT FOR IT... 👀`).
  3. 🎵 **Audio & Music**: Emotion-based AI auto music selection, custom MP3 uploads, and dynamic sidechain vocal ducking.
  4. 📐 **Framing & Trim**: Dynamic facecam splitting, blurred background fill, and precision `-1s` / `+1s` nudge trimming.
  5. 📋 **Social Metadata**: 1-click copy for **YouTube Shorts**, **TikTok**, **Instagram Reels**, and **X / Twitter**.

### 3. 👥 12-Director Autonomous Agency Syndicate
The engine organizes automated clipping into 12 specialized autonomous roles:
* **Executive Producer**: Orchestrates production slates and multi-channel cadence.
* **Strategic Plan Thinker**: Formulates duration ratios and content schedules.
* **Viral Idea Finder**: Meta research on trending topics and streamer highlights.
* **Algorithm & Retention Manager**: Optimizes watch curves (>90% target APV).
* **Channel Reach Specialist**: Mobile dark-mode contrast and high-ranking SEO.
* **Lead Acquisition Director**: Ingests official VODs and filters re-uploads.
* **Creative Director**: Curiosity-gap hook engineering.
* **Senior Visual Finishing Director**: NVIDIA NVENC 1080x1920 60FPS hardware export.
* **Sound Master**: EBU R128 (-14 LUFS) broadcast loudness mastering.
* **Art Director**: High-saturation keyframe extraction and mobile contrast.
* **Standards & Practices Director**: Eliminates corporate jargon and enforces vocabulary.
* **Global Distribution Lead**: Cloud scheduling and publishing management.

### 4. ☁️ Zero-PC Disk Cloud CDN Offloading
* Automatically offloads finished multi-gigabyte video packages to Cloud CDN.
* Purges local raw VODs and temporary files instantly to keep your PC storage 100% free.

### 5. 🛡️ Safe Staging Mode
* Built-in freeze guard (`POSTING_ENABLED = False`) allows you to generate and review hundreds of clips safely before publishing anything publicly.

---

## 🚀 Quick Start Guide

### Prerequisites
1. **Python 3.10+** installed.
2. **FFmpeg** installed and added to your system PATH:
   * **Windows**: `winget install Gyan.FFmpeg`
   * **Mac**: `brew install ffmpeg`
   * **Linux**: `sudo apt install ffmpeg`
3. *(Recommended)* **Ollama** installed with Llama 3.2:
   ```bash
   ollama pull llama3.2:latest
   ```

### 1-Click Launch (Windows)
Simply double-click:
```bash
start.bat
```
*(Or double-click `install.bat` if running for the first time)*

Or execute in PowerShell:
```powershell
.\launch.ps1
```
This automatically starts Ollama, spins up the PeakCut FastAPI server, initializes the background autonomous engine, and opens your browser to `http://127.0.0.1:8765/dashboard`.

---

## 🤖 Google Antigravity Integration (Zero-Config)

PeakCut features native **Google Antigravity Agent** integration (`.agents/skills/peakcut` and `GEMINI.md`).

### How to use it in Google Antigravity:
1. **Open Google Antigravity** and clone/open this repository:
   ```bash
   git clone https://github.com/JunaidKhan-7860/PeakCut.git
   ```
2. **Open the `PeakCut` folder** as your workspace in Antigravity.
   * Antigravity automatically discovers the built-in skill (`.agents/skills/peakcut/SKILL.md`) and project guidelines (`GEMINI.md`).
3. **Just prompt Antigravity in plain English**:
   * *"Start PeakCut"* or *"Install and run PeakCut"*
   * *"Open my clipping dashboard"*
   * *"Clip this YouTube stream: <URL>"*
   * *"Check status of staged clips"*
   * *"Stop PeakCut and free up GPU"*

Antigravity executes the setup and launch scripts automatically, detects your hardware, and keeps you updated right inside your chat!

---

### Manual Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/JunaidKhan-7860/PeakCut.git
   cd PeakCut
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Mac/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize configuration:**
   ```bash
   cp .env.example .env
   ```

5. **Start the studio server:**
   ```bash
   python -m studio.server
   ```
   Open your browser to:
   * **Live Dashboard**: [http://127.0.0.1:8765/dashboard](http://127.0.0.1:8765/dashboard)
   * **Studio Workspace**: [http://127.0.0.1:8765/app](http://127.0.0.1:8765/app)

6. **(Optional) Run 24/7 Autonomous Clipping Engine:**
   ```bash
   python autonomous_engine.py
   ```

---

## 📁 Repository Structure

```
PeakCut/
├── studio/                  # Core video & backend pipeline
│   ├── server.py            # FastAPI web server & REST endpoints
│   ├── render.py            # FFmpeg NVENC 1080x1920 60FPS video compositor
│   ├── facecam.py           # Computer vision facecam isolation & layout
│   ├── brain.py             # Llama 3.2 neural scoring & hook prompts
│   ├── transcribe.py        # Whisper word-by-word ASR transcription
│   ├── cloud_storage.py     # Cloud CDN sync & PC storage zero-disk cleaner
│   ├── roles.py             # 12-Director autonomous agency syndicate
│   ├── rights.py            # Editorial standards & rights verification
│   └── uploader.py          # Staged clip packaging & distribution
├── web/                     # Frontend user interface
│   ├── dashboard.html       # Obsidian dark mode live control dashboard
│   ├── index.html           # Full studio editor with 9:16 mobile mockup
│   └── staged.html          # Staged review page
├── config/                  # Configuration & licensing models
├── autonomous_engine.py     # 24/7 autonomous VOD discovery & clipping daemon
├── auto_poster.py           # Release scheduler with safe freeze guard
├── launch.ps1               # 1-click PowerShell launcher
├── start.bat                # 1-click Windows batch launcher
├── requirements.txt         # Python package dependencies
└── README.md                # Comprehensive documentation
```

---

## 🛡️ License

PeakCut is released under the **MIT License**. Free for personal and commercial content creation.

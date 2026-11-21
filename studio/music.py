"""Background music library and audio mixing with intelligent speech ducking."""
import json
import os
import re
import urllib.request
from pathlib import Path
from . import config

MUSIC_DIR = config.DATA_DIR / "music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

TRACKS = {
    "none": {"label": "Off (No Music)", "file": None, "genre": "none"},
    "auto": {"label": "✨ AI Auto-Pick (by emotion)", "file": None, "genre": "auto"},
    "hype": {"label": "🔥 Hype Phonk (Clutches & Rage)", "file": "hype_phonk.mp3", "genre": "action"},
    "funny": {"label": "😂 Funny Bounce (Comedy & Fails)", "file": "funny_bounce.mp3", "genre": "comedy"},
    "dramatic": {"label": "😱 Dramatic Suspense (Shock & Mystery)", "file": "dramatic_suspense.mp3", "genre": "suspense"},
    "chill": {"label": "☕ Chill Lo-Fi (Story & Banter)", "file": "chill_lofi.mp3", "genre": "lofi"},
    "epic": {"label": "🏆 Epic Victory (Wins & W Moments)", "file": "epic_victory.mp3", "genre": "triumphant"},
}

def list_tracks() -> dict:
    """Returns map of track IDs to display labels."""
    out = {k: v["label"] for k, v in TRACKS.items()}
    # Scan for custom user MP3s
    for p in MUSIC_DIR.glob("*.mp3"):
        stem = p.stem.lower()
        if stem not in [v["file"].replace(".mp3", "") for v in TRACKS.values() if v.get("file")]:
            out[stem] = f"🎵 {p.stem.replace('_', ' ').title()}"
    return out

def resolve_track(track_key: str, clip: dict = None) -> Path | None:
    """Returns absolute path to chosen music track, or None."""
    if not track_key or track_key == "none":
        return None

    if track_key == "auto":
        # AI heuristic based on clip category & score
        cat = str(clip.get("category", "")).lower() if clip else ""
        score = clip.get("score", 0) if clip else 0
        
        if cat in ("funny", "fail"):
            chosen = "funny"
        elif cat in ("clutch", "rage"):
            chosen = "hype"
        elif cat in ("shock", "take"):
            chosen = "dramatic"
        elif cat in ("story", "other"):
            chosen = "chill"
        elif score >= 85:
            chosen = "epic"
        else:
            chosen = "chill"
    else:
        chosen = track_key

    # Check preset
    preset = TRACKS.get(chosen)
    if preset and preset.get("file"):
        path = MUSIC_DIR / preset["file"]
        if path.exists():
            return path

    # Check custom file
    custom = MUSIC_DIR / f"{chosen}.mp3"
    if custom.exists():
        return custom

    # Fallback to chill or first mp3
    fallback = MUSIC_DIR / "chill_lofi.mp3"
    return fallback if fallback.exists() else None

def search_online(query: str, limit: int = 5) -> list[dict]:
    """Searches online open audio libraries for royalty-free tracks."""
    # Free Music Archive / Openverse API search
    url = f"https://api.openverse.org/v1/audio/?q={urllib.parse.quote(query)}&page_size={limit}&license_type=commercial"
    req = urllib.request.Request(url, headers={"User-Agent": "PeakCut/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for item in data.get("results", []):
                results.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "creator": item.get("creator"),
                    "url": item.get("url"),
                    "audio_url": item.get("audio_url") or item.get("url"),
                    "license": item.get("license")
                })
            return results
    except Exception:
        return []

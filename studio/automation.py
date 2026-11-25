"""Khan Clipping Automation: Watch Folder, Discord/Custom Webhook alerts, and Words-to-Avoid linter.

Settings live in DATA_DIR/preferences/automation.json. Respects the Safe Staging Mode guard:
webhooks announce clip metadata only (never auto-publish videos to YouTube/Instagram).
"""
import json
import re
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from . import config

VIDEO_EXT = (".mp4", ".mkv", ".mov", ".webm", ".m4v", ".avi", ".ts", ".flv")
_WATCH_STARTED = False
_WATCH_SEEN = {}

DEFAULTS = {
    "watch_on": False,
    "watch_folder": "",
    "watch_count": 4,
    "watch_mode": "fast",
    "webhook_url": "",
    "banned": [],
}
_LOCK = threading.RLock()


def _file() -> Path:
    return config.DATA_DIR / "preferences" / "automation.json"


def read() -> dict:
    p = _file()
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        cfg = {}
    return {**DEFAULTS, **(cfg if isinstance(cfg, dict) else {})}


def validate(body: dict) -> dict:
    out = {}
    if "watch_folder" in body:
        folder = str(body.get("watch_folder") or "").strip().strip('"')
        if folder and not Path(folder).is_dir():
            raise ValueError("That folder does not exist. Paste the full path of an existing folder.")
        out["watch_folder"] = folder
    if "watch_on" in body:
        out["watch_on"] = bool(body.get("watch_on"))
    if "watch_count" in body:
        out["watch_count"] = max(1, min(12, int(body.get("watch_count") or 4)))
    if "watch_mode" in body:
        m = body.get("watch_mode")
        out["watch_mode"] = m if m in ("fast", "balanced", "deep") else "fast"
    if "webhook_url" in body:
        url = str(body.get("webhook_url") or "").strip()
        if url:
            p = urlparse(url)
            local = (p.hostname or "").lower() in ("127.0.0.1", "localhost")
            if p.scheme not in ("https", "http") or not p.hostname or p.username or p.password or (p.scheme == "http" and not local) or len(url) > 400:
                raise ValueError("Use an https address (http only for localhost).")
        out["webhook_url"] = url
    if "banned" in body:
        words = body.get("banned") or []
        if isinstance(words, str):
            words = re.split(r"[,\n]+", words)
        if not isinstance(words, list) or len(words) > 300:
            raise ValueError("Use at most 300 words.")
        out["banned"] = [str(w).strip()[:40] for w in words if str(w).strip()][:300]
    if out.get("watch_on") and not (out.get("watch_folder") or read().get("watch_folder")):
        raise ValueError("Choose an existing folder to watch first.")
    return out


def save(body: dict) -> dict:
    with _LOCK:
        cfg = {**read(), **validate(body)}
        p = _file()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)
    return cfg


def lint(texts: list, banned: list | None = None) -> list:
    """Return any banned words found (whole-word, case-insensitive) inside texts."""
    words = read().get("banned") if banned is None else banned
    hay = " ".join(str(t or "") for t in texts).casefold()
    return sorted({
        w for w in words or []
        if w.strip() and re.search(r"(?<!\w)" + re.escape(w.strip().casefold()) + r"(?!\w)", hay)
    })


def notify(clip: dict):
    """Send non-blocking Discord or custom webhook alert when a clip is staged."""
    url = read().get("webhook_url")
    if not url:
        return

    def work():
        try:
            title = clip.get("title") or "New Khan Clipping Highlight"
            hook = clip.get("hook") or ""
            score = clip.get("score", "")
            payload = {
                "event": "clip_ready",
                "app": "KhanClipping",
                "content": f"⚡ **Khan Clipping** staged a new clip: **{title}** (Score: {score}/100)\n> {hook}".strip(),
                "title": title,
                "hook": hook,
                "score": score,
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url, body, {"Content-Type": "application/json", "User-Agent": "KhanClipping"})
            urllib.request.urlopen(req, timeout=8).read(1000)
        except Exception:
            pass

    threading.Thread(target=work, daemon=True).start()


def start_watcher(on_new_video):
    """Start background daemon polling the Watch Folder every 15s for newly finished recordings."""
    global _WATCH_STARTED
    with _LOCK:
        if _WATCH_STARTED:
            return
        _WATCH_STARTED = True

    def loop():
        while True:
            try:
                cfg = read()
                folder = Path(cfg.get("watch_folder") or "")
                if cfg.get("watch_on") and cfg.get("watch_folder") and folder.is_dir():
                    for f in folder.iterdir():
                        if not f.is_file() or f.suffix.lower() not in VIDEO_EXT:
                            continue
                        key = str(f.resolve())
                        if _WATCH_SEEN.get(key) == "done":
                            continue
                        try:
                            size = f.stat().st_size
                        except OSError:
                            continue
                        prev = _WATCH_SEEN.get(key)
                        if prev is None or prev != size or size < 1024:
                            _WATCH_SEEN[key] = size
                            continue
                        _WATCH_SEEN[key] = "done"
                        try:
                            on_new_video(f, cfg)
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(15)

    threading.Thread(target=loop, daemon=True, name="khan-watch-folder").start()

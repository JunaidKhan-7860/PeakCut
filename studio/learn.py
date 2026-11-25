"""Local 5-star preference ranker: user clip ratings adapt highlight feature weights locally.

Ratings (1-5 stars) are stored in DATA_DIR/preferences/feedback.jsonl. After 8+ rated clips, ridge
regression adapts weights toward the user's preferences while keeping everything 100% local.
"""
import json
import math
import threading
import time
from pathlib import Path

import numpy as np

from . import config

FEATURES = ["loud", "shout", "words", "motion", "flash", "strobe", "cuts", "llm", "chat", "replay", "bang"]
DEFAULT = {
    "loud": 0.17, "shout": 0.13, "words": 0.20, "motion": 0.17,
    "flash": 0.08, "strobe": 0.04, "cuts": 0.03, "llm": 0.18,
    "chat": 0.14, "replay": 0.16, "bang": 0.12,
}
MIN_RATINGS = 8
_LOCK = threading.RLock()


def _paths() -> tuple[Path, Path]:
    d = config.DATA_DIR / "preferences"
    return d / "feedback.jsonl", d / "weights.json"


def load_weights() -> dict:
    _, wp = _paths()
    try:
        w = json.loads(wp.read_text(encoding="utf-8"))
        if not isinstance(w, dict):
            raise ValueError("Invalid learned weights")
        result = {k: float(w.get(k, DEFAULT[k])) for k in FEATURES}
        if not all(math.isfinite(v) and v > 0 for v in result.values()):
            raise ValueError("Invalid learned weights")
        return result
    except (OSError, ValueError, TypeError):
        return dict(DEFAULT)


def ratings() -> list:
    fp, _ = _paths()
    out = []
    if fp.exists():
        for line in fp.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    latest = {}
    for row in out:
        if not isinstance(row, dict) or not row.get("clip_id") or row.get("rating") not in (1, 2, 3, 4, 5):
            continue
        latest[row["clip_id"]] = row
    return list(latest.values())


def summary() -> dict:
    rows = ratings()
    _, wp = _paths()
    fitted = wp.exists() and len(rows) >= MIN_RATINGS
    return {
        "ratings": len(rows),
        "min_ratings": MIN_RATINGS,
        "fitted": fitted,
        "weights": load_weights(),
        "by_clip": {r["clip_id"]: r["rating"] for r in rows},
        "message": (
            "Preference model adapted from your ratings."
            if fitted else f"Rate {max(0, MIN_RATINGS - len(rows))} more clips to personalise moment picking."
        ),
    }


def record(clip_id: str, rating: int, features: dict | None = None, extra: dict | None = None) -> dict:
    if not clip_id or rating not in (1, 2, 3, 4, 5):
        raise ValueError("Choose a clip and a rating from 1 to 5.")
    clean_feat = {k: float(features[k]) for k in FEATURES if isinstance(features, dict) and features.get(k) is not None}
    if not clean_feat:
        clean_feat = {"loud": 0.6, "words": 0.6, "llm": min(1.0, rating / 5.0)}
    fp, wp = _paths()
    fp.parent.mkdir(parents=True, exist_ok=True)
    row = {"t": int(time.time()), "clip_id": str(clip_id), "rating": int(rating), "features": clean_feat, **(extra or {})}
    with _LOCK:
        with fp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return _refit(wp)


def _refit(wp: Path) -> dict:
    rows = ratings()
    n = len(rows)
    out = {
        "ratings": n,
        "min_ratings": MIN_RATINGS,
        "weights": dict(DEFAULT),
        "fitted": False,
        "insight": [],
        "by_clip": {r["clip_id"]: r["rating"] for r in rows},
        "message": f"Rate {max(0, MIN_RATINGS - n)} more clips to personalise moment picking.",
    }
    if n >= MIN_RATINGS:
        X = np.array([
            [float(r["features"].get(k)) if r["features"].get(k) is not None else np.nan for k in FEATURES]
            for r in rows
        ])
        for col in range(len(FEATURES)):
            obs = X[:, col][np.isfinite(X[:, col])]
            X[~np.isfinite(X[:, col]), col] = float(obs.mean()) if len(obs) else 0.0
        y = np.array([(r["rating"] - 3) / 2.0 for r in rows])
        if y.std() >= 1e-6 and np.any(X.std(axis=0) > 1e-6):
            w0 = np.array([DEFAULT[k] for k in FEATURES])
            w0 = w0 / w0.sum()
            Xc = X - X.mean(axis=0)
            wf = np.clip(np.linalg.solve(Xc.T @ Xc + 2.0 * np.eye(len(FEATURES)), Xc.T @ y + 2.0 * w0), 0.01, None)
            wf = wf / wf.sum()
            alpha = min(0.85, n / 60.0)
            w = (1 - alpha) * w0 + alpha * wf
            w = w / w.sum()
            out["weights"] = {k: round(float(v), 4) for k, v in zip(FEATURES, w)}
            out["fitted"] = True
            out["message"] = "Preferences updated from your rated moments."
        else:
            out["message"] = "Rate a mix of higher and lower clips so the ranker can compare."
    wp.parent.mkdir(parents=True, exist_ok=True)
    tmp = wp.with_suffix(".tmp")
    tmp.write_text(json.dumps(out["weights"], ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(wp)
    return out

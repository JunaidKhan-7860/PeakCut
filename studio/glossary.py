"""Your Words ("Always fix") dictionary: fix a spelling once and every future clip uses it automatically.

Stored locally in DATA_DIR/preferences/glossary.json. Supports up to 500 1-to-3 word replacements while
preserving exact per-word timestamps in captions.
"""
import json
import re
import threading
from pathlib import Path

from . import config
from .loanwords import _norm

MAX_ENTRIES = 500
_LOCK = threading.Lock()
_CACHE = {"mtime": None, "path": None, "entries": []}
_EDGE = re.compile(r"^((?:[^\w\u0900-\u097f]|[।॥])*)(.*?)((?:[^\w\u0900-\u097f]|[।॥])*)$", re.S)


def _path() -> Path:
    return config.DATA_DIR / "preferences" / "glossary.json"


def _key(text: str) -> str:
    return " ".join(_norm(str(text)).casefold().split())


def _clean(value: str, name: str) -> str:
    value = " ".join(str(value or "").split())
    if not 1 <= len(value) <= 60:
        raise ValueError(f"{name}: use 1-60 characters.")
    if len(value.split()) > 3:
        raise ValueError(f"{name}: at most 3 words.")
    return value


def entries() -> list:
    """Return [{'from': ..., 'to': ...}], newest first."""
    p = _path()
    if not p.exists():
        return []
    mtime = p.stat().st_mtime
    if _CACHE["mtime"] != mtime or _CACHE["path"] != str(p):
        try:
            rows = json.loads(p.read_text(encoding="utf-8"))
            _CACHE["entries"] = [r for r in rows if isinstance(r, dict) and r.get("from") and r.get("to")]
        except (OSError, ValueError):
            _CACHE["entries"] = []
        _CACHE["mtime"] = mtime
        _CACHE["path"] = str(p)
    return list(_CACHE["entries"])


def _save(rows: list):
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_suffix(".tmp")
    temp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(p)
    _CACHE["entries"] = list(rows)
    _CACHE["mtime"] = p.stat().st_mtime
    _CACHE["path"] = str(p)


def add(wrong: str, right: str) -> list:
    """Add or update a global replacement rule."""
    wrong, right = _clean(wrong, "Written as"), _clean(right, "Should be")
    if _key(wrong) == _key(right) and wrong == right:
        raise ValueError("Both sides are the same.")
    with _LOCK:
        rows = [r for r in entries() if _key(r["from"]) != _key(wrong)]
        if len(rows) >= MAX_ENTRIES:
            raise ValueError(f"At most {MAX_ENTRIES} words. Remove one first.")
        rows.insert(0, {"from": wrong, "to": right})
        _save(rows)
    return rows


def remove(wrong: str) -> list:
    """Delete a replacement rule by its source phrase."""
    with _LOCK:
        rows = [r for r in entries() if _key(r["from"]) != _key(wrong)]
        _save(rows)
    return rows


def _table(rows: list) -> dict:
    table = {}
    for r in rows:
        table.setdefault(len(r["from"].split()), {})[_key(r["from"])] = r["to"]
    return table


def _word_field(words: list) -> str:
    if not words:
        return "w"
    return "w" if "w" in words[0] else "text"


def fix_text(text: str, rows=None) -> str:
    """Apply glossary replacements to a title, hook, or plain string."""
    rows = entries() if rows is None else rows
    if not rows or not text:
        return text
    ws = [{"w": t, "s": 0.0, "e": 0.0} for t in str(text).split()]
    return " ".join(w["w"] for w in fix_words(ws, rows))


def fix_words(words: list, rows=None) -> list:
    """Apply glossary replacements to timed caption words ({'w','s','e'} or {'text','start','end'})."""
    rows = entries() if rows is None else rows
    if not rows or not words:
        return words
    tk = _word_field(words)
    ek = "e" if "e" in words[0] else "end"
    table = _table(rows)
    lengths = sorted(table, reverse=True)
    out, i = [], 0
    while i < len(words):
        for n in lengths:
            if i + n > len(words):
                continue
            parts = [_EDGE.match(str(w.get(tk, ""))).groups() for w in words[i:i + n]]
            core = " ".join(p[1] for p in parts)
            hit = table[n].get(_key(core))
            if hit is not None:
                lead, tail = parts[0][0], parts[-1][2]
                updated = dict(words[i])
                updated[tk] = lead + hit + tail
                updated[ek] = words[i + n - 1].get(ek, words[i].get(ek))
                out.append(updated)
                i += n
                break
        else:
            out.append(words[i])
            i += 1
    return out

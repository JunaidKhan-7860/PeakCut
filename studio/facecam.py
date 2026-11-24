"""Where the facecam is.

A gaming stream is a game with a small webcam picture in one corner of it. The
short that comes out of it is better when the game fills the screen and the
webcam sits in the corner of it, instead of the whole 16:9 frame squeezed into
a band with blurred fill above and below.

The webcam is found by the one thing a webcam always has and a game almost never
has: a straight border that stays in the same place in every frame. A wall in
the game moves, a HUD bar changes, but the edge of the webcam box does not move
at all. A second thing tells the webcam apart from the game's own panels, which
have straight borders too: the picture inside a webcam is almost still, while
the game behind a panel keeps moving.

Metric: for every column and every row, how much the picture changes at that
line, counted over frames spread through the video. A border of the webcam box
stands out from the rest.

One frame can also be shown to the AI (`detect(path, ask=...)`), which is better
than any measurement at telling a person from a game character. Its answer is
measured again on the picture before it is used, so being wrong costs a search,
not a clip.

Only numpy and ffmpeg, which are already here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

W, H = 320, 180            # the picture is looked at small: only the lines matter
MAX_FRAMES = 24            # frames spread through the video
MIN_SIZE = 0.12            # the smallest a webcam may be, as a part of the width or height
MAX_SIZE = 0.60            # and the largest
ASPECT_MIN = 0.55          # the narrowest: a phone held upright is about 0.56
ASPECT_MAX = 3.20          # the widest: a banner or a ticker is wider than this
STILL_FRAC = 0.35          # how much of the game's own movement a webcam picture may have
STILL_MIN = 6.0            # and the floor, for a game that itself is almost still
STILL_SHARE = 0.30         # at most this much of a webcam picture may be moving, or the game is showing through
EDGE_FLUSH = 0.02          # a side this close to the frame's own edge is the edge
MATCH = 0.35               # how much a box the AI points at must cover a measured box to be that box
EDGE = 2.2                 # how much brighter than the average line a border must be


def _frames(path: str | Path, count: int = MAX_FRAMES) -> np.ndarray:
    """The video as a few grey frames, spread through it."""
    try:
        dur = _duration(path)
        rate = max(count / dur, 0.02) if dur > 0 else 0.2
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(path),
             "-vf", f"fps={rate:.4f},scale={W}:{H},format=gray",
             "-frames:v", str(count), "-f", "rawvideo", "-"],
            capture_output=True, timeout=180)
    except Exception:  # noqa: BLE001 - no ffmpeg or an unreadable file: no facecam, not a failure
        return np.zeros((0, H, W), dtype=np.uint8)
    raw = proc.stdout or b""
    size = W * H
    n = len(raw) // size
    if n < 4:
        return np.zeros((0, H, W), dtype=np.uint8)
    return np.frombuffer(raw[:n * size], dtype=np.uint8).reshape(n, H, W)


def _duration(path: str | Path) -> float:
    try:
        proc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                               "-of", "default=nw=1:nk=1", str(path)],
                              capture_output=True, text=True, timeout=60)
        return float((proc.stdout or "").strip() or 0)
    except Exception:  # noqa: BLE001
        return 0.0


def _profiles(frames: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(vertical lines, horizontal lines): how much changes at each column and each row.

    The median over the frames is used, so one busy moment cannot invent a line."""
    if len(frames) < 4:
        return np.zeros(W), np.zeros(H)
    f = frames.astype(np.int16)
    gx = np.median(np.abs(np.diff(f, axis=2)).sum(axis=1), axis=0)   # change across each column boundary
    gy = np.median(np.abs(np.diff(f, axis=1)).sum(axis=2), axis=0)   # change across each row boundary
    return gx, gy


def _peaks(profile: np.ndarray, limit: int) -> list[tuple[int, float]]:
    """The lines that stand out: (where, how much)."""
    if len(profile) < 3:
        return []
    med = float(np.median(profile)) or 1.0
    out = []
    for i in range(1, len(profile) - 1):
        if profile[i] >= profile[i - 1] and profile[i] > profile[i + 1] and profile[i] > EDGE * med:
            out.append((i, float(profile[i] / med)))
    return sorted(out, key=lambda p: -p[1])[:limit]


def _size(path: str | Path) -> tuple[int, int]:
    proc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                           "-show_entries", "stream=width,height", "-of", "default=nw=1", str(path)],
                          capture_output=True, text=True, timeout=60)
    w = h = 0
    for line in (proc.stdout or "").splitlines():
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        try:
            if k.strip() == "width":
                w = int(v.strip())
            elif k.strip() == "height":
                h = int(v.strip())
        except ValueError:
            continue
    return w, h


def _stillness(frames: np.ndarray) -> np.ndarray:
    """How much each pixel changes over the frames.

    A webcam picture barely changes: a person sits in a room and shifts a little. The game changes every
    frame. This is the one thing that tells a webcam apart from the game's own panels, which have straight
    borders too and are drawn over the game with the game showing through them."""
    return frames.astype(np.float32).std(axis=0)


def _plausible(x0, y0, x1, y1, still, light, game, share=STILL_SHARE):
    """Could this rectangle be a webcam picture? Judged on its shape, its stillness and its light.

    Returns how much it moves, or None. Nothing here says which corner it is in: a webcam may sit in a
    corner, along one edge, or with a margin all round."""
    bw, bh = (x1 - x0) / W, (y1 - y0) / H
    if not (MIN_SIZE <= bw <= MAX_SIZE and MIN_SIZE <= bh <= MAX_SIZE):
        return None
    # measured in pixels: a 4:3 picture is 1.33, a phone held upright is 0.56
    aspect = (bw * W) / max(1e-6, bh * H)
    if not (ASPECT_MIN <= aspect <= ASPECT_MAX):
        return None
    a, b, c, d = int(x0), int(y0), int(x1), int(y1)
    inside = still[b:d, a:c]
    if not inside.size:
        return None
    cut = max(STILL_MIN, STILL_FRAC * game)
    moving = float(np.median(inside))
    if moving > cut:
        return None                    # it changes with the game: it is the game
    if float((inside > cut).mean()) > share:
        return None                    # a good part of it moves: the game is showing through
    if float(light[b:d, a:c].mean()) < 0.30 * float(light.mean()):
        return None                    # a black hole, not a picture
    return moving


def _local(vpeaks, hpeaks, still, light):
    """Every rectangle the strong straight lines can make, that still looks like a camera.

    Returns them best first: the one whose weakest border is the strongest, and of those the bigger."""
    game = float(np.median(still))
    xs = sorted({0.0, float(W)} | {float(x) for x, _ in vpeaks[:10]})
    ys = sorted({0.0, float(H)} | {float(y) for y, _ in hpeaks[:10]})
    vs = {float(x): s for x, s in vpeaks}
    hs = {float(y): s for y, s in hpeaks}
    out = []
    for i, x0 in enumerate(xs):
        wx = [vs[v] for v in (x0,) if v in vs]
        for x1 in xs[i + 1:]:
            wscore = wx + [vs[v] for v in (x1,) if v in vs]
            for j, y0 in enumerate(ys):
                hy0 = [hs[v] for v in (y0,) if v in hs]
                for y1 in ys[j + 1:]:
                    score = wscore + hy0 + [hs[v] for v in (y1,) if v in hs]
                    if len(score) < 2:
                        continue       # a box needs two borders of its own, or it is just the frame
                    moving = _plausible(x0, y0, x1, y1, still, light, game)
                    if moving is None:
                        continue
                    key = (min(score), (x1 - x0) * (y1 - y0))
                    out.append({"key": key, "x": x0, "y": y0, "x1": x1, "y1": y1,
                                "score": round(min(score), 2), "moving": moving})
    return sorted(out, key=lambda c: c["key"], reverse=True)


def _overlap(a, box) -> float:
    """How much two boxes cover the same ground: 1 when they are the same, 0 when they do not touch."""
    ax0, ay0, ax1, ay1 = a["x"], a["y"], a["x1"], a["y1"]
    bx, by, bw, bh = box
    bx0, by0, bx1, by1 = bx * W, by * H, (bx + bw) * W, (by + bh) * H
    ix = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = ix * iy
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / union if union > 0 else 0.0


def _full_frame(path: str | Path) -> np.ndarray | None:
    """One grey frame at full size, from the middle of the video: where the borders are measured."""
    w, h = _size(path)
    if not w or not h:
        return None
    try:
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, _duration(path) / 2.0):.1f}", "-i", str(path),
             "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
            capture_output=True, timeout=120).stdout or b""
    except Exception:  # noqa: BLE001
        return None
    if len(raw) < w * h:
        return None
    return np.frombuffer(raw[:w * h], dtype=np.uint8).reshape(h, w).astype(np.float32)


def _best(profile: np.ndarray, approx: float, span: float) -> float:
    """The strongest change near a guessed line."""
    lo, hi = max(0, int(approx - span)), min(len(profile), int(approx + span) + 1)
    seg = profile[lo:hi]
    return float(lo + seg.argmax()) if len(seg) else float(approx)


def _snap(path: str | Path, box, w: int, h: int, span: float = 0.0):
    """A box on the small grid, put onto the borders that are really in the picture.

    A border the small grid found is a pixel or two out; a box a model proposed can be a good part of the
    frame out, which is what `span` is for. A side within a hair of the frame's own edge is the edge."""
    frame = _full_frame(path)
    if frame is None:
        return None
    fh, fw = frame.shape
    col = np.abs(np.diff(frame, axis=1)).sum(axis=0)
    row = np.abs(np.diff(frame, axis=0)).sum(axis=1)
    # The small grid is a quarter of the picture, so a border found on it is a few pixels out; one the
    # model proposed can be a good part of the frame out, which is what `span` is for.
    spread = max(4.0, span * max(fw, fh), 1.5 * max(fw / W, fh / H))

    def line(profile, approx, edge, extent):
        if abs(approx - edge) <= EDGE_FLUSH * extent:
            return float(edge)
        return _best(profile, approx, spread)

    x0, y0, x1, y1 = box
    return (line(col, x0 * fw / W, 0, fw), line(row, y0 * fh / H, 0, fh),
            line(col, x1 * fw / W, fw, fw), line(row, y1 * fh / H, fh, fh))


def _corner(x0, y0, x1, y1, w, h) -> str:
    """What part of the frame the box is on: its corner, its edge, or the middle."""
    near = EDGE_FLUSH
    left, right = x0 <= w * near, x1 >= w * (1 - near)
    top, bottom = y0 <= h * near, y1 >= h * (1 - near)
    if left and top:
        return "top-left"
    if right and top:
        return "top-right"
    if left and bottom:
        return "bottom-left"
    if right and bottom:
        return "bottom-right"
    if left or right:
        return "right" if right else "left"
    if top or bottom:
        return "bottom" if bottom else "top"
    return "middle"


def _finish(path: str | Path, found: dict, w: int, h: int, still: np.ndarray) -> dict | None:
    """The box in source pixels, with how sure it is that this is really a camera."""
    snapped = _snap(path, (found["x"], found["y"], found["x1"], found["y1"]), w, h)
    if not snapped:
        return None
    x0, y0, x1, y1 = snapped
    if x1 - x0 < w * MIN_SIZE or y1 - y0 < h * MIN_SIZE:
        return None
    inside = still[int(found["y"]):int(found["y1"]), int(found["x"]):int(found["x1"])]
    game = float(np.median(still))
    moving = float(np.median(inside)) if inside.size else 99.0
    # sure of it when the picture inside hardly moves while the game around it is racing
    conf = "high" if moving <= max(3.0, 0.25 * game) else "low"
    return {"x": int(round(x0)), "y": int(round(y0)), "w": int(round(x1 - x0)), "h": int(round(y1 - y0)),
            "corner": _corner(x0, y0, x1, y1, w, h), "score": found.get("score", 0.0), "conf": conf}


def _frame_jpeg(path: str | Path, width: int = 768) -> bytes:
    """One frame of the stream, small, as a JPEG: what a model is shown."""
    try:
        return subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, _duration(path) / 2.0):.1f}", "-i", str(path),
             "-frames:v", "1", "-vf", f"scale={width}:-2", "-pix_fmt", "yuvj420p", "-q:v", "4",
             "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
            capture_output=True, timeout=120).stdout or b""
    except Exception:  # noqa: BLE001
        return b""


def _asked(path: str | Path, ask):
    """One frame to the model: (did it look, its box as parts of the frame or None)."""
    jpeg = _frame_jpeg(path)
    if not jpeg:
        return False, None
    try:
        answer = ask(jpeg) or {}
    except Exception:  # noqa: BLE001 - a model that cannot look is not a failure
        return False, None
    return bool(answer.get("looked")), answer.get("box")


def _seen(path: str | Path, box, w: int, h: int, still: np.ndarray, light: np.ndarray) -> dict | None:
    """A box the model proposed, put onto the picture's real borders and checked like any other.

    A model reads a picture well but places a box roughly, and it can be wrong about the whole thing. So
    its box is only believed where the borders are really there and the picture inside really is still."""
    fx, fy, fw, fh = box
    snapped = _snap(path, (fx * W, fy * H, (fx + fw) * W, (fy + fh) * H), w, h, span=0.12)
    if not snapped:
        return None
    x0, y0, x1, y1 = snapped
    if x1 - x0 < w * MIN_SIZE or y1 - y0 < h * MIN_SIZE:
        return None
    small = (x0 * W / w, y0 * H / h, x1 * W / w, y1 * H / h)
    # The model has already said a person is here, so the picture inside is allowed to move more than a
    # measured box would be; what it may not be is the game itself.
    if _plausible(*small, still, light, float(np.median(still)), share=1.0) is None:
        return None
    found = {"x": small[0], "y": small[1], "x1": small[2], "y1": small[3], "score": 0.0}
    return _finish(path, found, w, h, still)


CREATOR_FACECAM_PRESETS = {
    "carry": {"corner": "bottom-right", "rel": (0.72, 0.58, 0.27, 0.40)},
    "carryislive": {"corner": "bottom-right", "rel": (0.72, 0.58, 0.27, 0.40)},
    "carryminati": {"corner": "bottom-right", "rel": (0.72, 0.58, 0.27, 0.40)},
    "techno": {"corner": "top-left", "rel": (0.01, 0.02, 0.28, 0.38)},
    "technogamerz": {"corner": "top-left", "rel": (0.01, 0.02, 0.28, 0.38)},
    "techno-gamerz": {"corner": "top-left", "rel": (0.01, 0.02, 0.28, 0.38)},
    "mythpat": {"corner": "top-left", "rel": (0.01, 0.02, 0.28, 0.38)},
    "asianjeff": {"corner": "bottom-right", "rel": (0.72, 0.60, 0.27, 0.38)},
    "speed": {"corner": "top-right", "rel": (0.70, 0.02, 0.29, 0.40)},
    "ishowspeed": {"corner": "top-right", "rel": (0.70, 0.02, 0.29, 0.40)},
    "kai": {"corner": "top-right", "rel": (0.68, 0.02, 0.30, 0.42)},
    "kaicenat": {"corner": "top-right", "rel": (0.68, 0.02, 0.30, 0.42)},
    "kai-cenat": {"corner": "top-right", "rel": (0.68, 0.02, 0.30, 0.42)},
    "casetoo": {"corner": "top-left", "rel": (0.01, 0.02, 0.28, 0.38)},
    "totalgaming": {"corner": "bottom-right", "rel": (0.70, 0.58, 0.28, 0.40)},
    "total-gaming": {"corner": "bottom-right", "rel": (0.70, 0.58, 0.28, 0.40)},
    "dom": {"corner": "bottom-right", "rel": (0.72, 0.58, 0.27, 0.40)},
    "dasgasdom3": {"corner": "bottom-right", "rel": (0.72, 0.58, 0.27, 0.40)}
}


YUNET_MODEL_PATH = Path("C:/peakcut/data/models/face_detection_yunet_2023mar.onnx")


def _get_yunet_detector(w: int, h: int, score_thresh: float = 0.60):
    if not YUNET_MODEL_PATH.is_file():
        return None
    try:
        import cv2
        if hasattr(cv2, "FaceDetectorYN_create"):
            return cv2.FaceDetectorYN_create(str(YUNET_MODEL_PATH), "", (w, h), score_threshold=score_thresh, nms_threshold=0.3)
    except Exception:
        pass
    return None


def verify_face_in_region(path: str | Path, box: list | tuple, min_hits: int = 2) -> bool:
    """Verifies with YuNet face detection that a human face actually exists in the specified box.
    Samples up to 8 frames across the video and checks if at least min_hits frames contain a human face.
    Prevents false facecam cropping on videos where the streamer is absent or not using a webcam."""
    if not path or not Path(path).is_file() or not box or len(box) != 4:
        return False
    bx, by, bw, bh = box
    if bw <= 15 or bh <= 15:
        return False
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return False
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        dur = total / fps if fps > 0 else 0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if dur < 0.5 or w == 0 or h == 0:
            cap.release()
            return False

        # Clamp box to video frame
        bx = max(0, min(w - 15, int(bx)))
        by = max(0, min(h - 15, int(by)))
        bw = max(15, min(w - bx, int(bw)))
        bh = max(15, min(h - by, int(bh)))

        detector = _get_yunet_detector(bw, bh, score_thresh=0.60)
        if detector is None:
            cap.release()
            return False

        samples = np.linspace(0.2, max(0.2, dur - 0.2), num=min(8, max(4, int(dur // 2))))
        hits = 0
        for t in samples:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            crop = frame[by:by+bh, bx:bx+bw]
            if crop.size == 0:
                continue
            detector.setInputSize((crop.shape[1], crop.shape[0]))
            retval, faces = detector.detect(crop)
            if faces is not None and len(faces) > 0:
                for face in faces:
                    if float(face[-1]) >= 0.60:
                        hits += 1
                        break
        cap.release()
        return hits >= min_hits
    except Exception:
        return False


def evaluate_reaction_quality(video_path: str | Path, face_box: list | tuple,
                              clip_meta: dict = None, words: list = None) -> tuple[bool, float, dict]:
    """Judges whether a streamer face reaction in this specific clip is high-value / expressive enough
    to warrant splitting the screen into a 42% facecam + 58% gameplay layout, or if the streamer is
    deadpan / motionless / unengaged, in which case full-screen 9:16 gameplay is superior.

    Returns (is_good_reaction, score, details_dict)."""
    if not video_path or not Path(video_path).is_file() or not face_box or len(face_box) != 4:
        return False, 0.0, {"verdict": "no_face_box"}

    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return False, 0.0, {"verdict": "cannot_open_video"}

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        dur = total / fps if fps > 0 else 0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if dur < 0.5 or w == 0 or h == 0:
            cap.release()
            return False, 0.0, {"verdict": "invalid_duration_or_dims"}

        bx, by, bw, bh = face_box
        bx = max(0, min(w - 15, int(bx)))
        by = max(0, min(h - 15, int(by)))
        bw = max(15, min(w - bx, int(bw)))
        bh = max(15, min(h - by, int(bh)))

        # Sample 12-16 frames evenly across the clip
        samples = np.linspace(0.3, max(0.3, dur - 0.3), num=min(16, max(6, int(dur * 1.2))))
        crops = []
        for t in samples:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            crop = frame[by:by+bh, bx:bx+bw]
            if crop.size > 0:
                small = cv2.resize(crop, (128, 128))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                crops.append(gray)
        cap.release()

        if len(crops) < 4:
            return False, 0.0, {"verdict": "insufficient_frames"}

        # 1. Physical motion inside facecam box (expressions, head shaking, laughing, body shifts)
        diffs = [float(np.mean(cv2.absdiff(crops[i], crops[i-1]))) for i in range(1, len(crops))]
        mean_motion = float(np.mean(diffs))
        max_motion = float(np.max(diffs))

        stack = np.stack(crops, axis=0).astype(np.float32)
        overall_variance = float(np.mean(np.std(stack, axis=0)))
        motion_score = round(mean_motion * 0.45 + max_motion * 0.25 + overall_variance * 0.30, 2)

        # 2. Vocal / Semantic excitement in clip transcript and titles
        vocal_bonus = 0.0
        text_content = ""
        if words:
            text_content = " ".join(str(w.get("w", "")) for w in words).upper()
        if clip_meta:
            text_content += " " + str(clip_meta.get("title", "")).upper() + " " + str(clip_meta.get("hook", "")).upper()

        reaction_triggers = (
            "!", "?", "BRO", "NO", "WTF", "OMG", "DEAD", "WHAT", "CRAZY", "WAIT",
            "LOOK", "RUN", "LAUGH", "HAHA", "LMAO", "OH", "DAMN", "SHIT", "HOLY", "WOW",
            "BHAI", "MAR", "PAGAL"
        )
        hits = sum(1 for trigger in reaction_triggers if trigger in text_content)
        if hits > 0:
            vocal_bonus = min(15.0, hits * 3.0)

        # Category cues
        cat = str(clip_meta.get("category", "")).lower() if clip_meta else ""
        if cat in ("funny", "rage", "shock", "reaction"):
            vocal_bonus += 5.0
        elif cat in ("cinematic", "scenic", "driving", "trailer"):
            vocal_bonus -= 6.0

        total_score = round(motion_score + vocal_bonus, 2)

        # Threshold:
        # An active, valuable streamer reaction has motion_score >= 12.0 OR (motion_score >= 8.0 with vocal excitement >= 6.0)
        # A deadpan, motionless streamer has motion_score < 8.0 and minimal vocal excitement.
        is_good_reaction = bool(motion_score >= 12.0 or (motion_score >= 8.0 and vocal_bonus >= 6.0))

        details = {
            "is_good_reaction": is_good_reaction,
            "total_score": total_score,
            "motion_score": motion_score,
            "mean_motion": round(mean_motion, 2),
            "max_motion": round(max_motion, 2),
            "variance": round(overall_variance, 2),
            "vocal_bonus": vocal_bonus,
            "verdict": "active_reaction_use_facecam" if is_good_reaction else "passive_face_prefer_full_gameplay"
        }
        return is_good_reaction, total_score, details
    except Exception:
        return False, 0.0, {"verdict": "evaluation_error"}


def _detect_faces_cv(path: str | Path) -> dict | None:
    """Uses YuNet deep neural network face detector to locate the persistent streamer facecam box."""
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return None
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        dur = total / fps if fps > 0 else 0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if dur < 1.0 or w == 0 or h == 0:
            cap.release()
            return None

        detector = _get_yunet_detector(w, h, score_thresh=0.65)
        if detector is None:
            cap.release()
            return None

        samples = np.linspace(0.5, max(0.5, dur - 0.5), num=min(14, max(6, int(dur // 2))))
        detections = []
        for t in samples:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            detector.setInputSize((w, h))
            retval, faces = detector.detect(frame)
            if faces is not None:
                for face in faces:
                    fx, fy, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                    score = float(face[-1])
                    # Streamer face must be at least 4% of dimension to avoid tiny game pedestrians
                    if score >= 0.65 and fw >= min(w, h) * 0.04 and fh >= min(w, h) * 0.04:
                        detections.append((fx, fy, fw, fh, score))
        cap.release()

        if not detections:
            return None

        # Cluster detections that appear near the same location across frames
        clusters = []
        for d in detections:
            matched = False
            for c in clusters:
                cx, cy = d[0] + d[2] / 2, d[1] + d[3] / 2
                if abs(cx - c['cx']) < w * 0.12 and abs(cy - c['cy']) < h * 0.12:
                    c['count'] += 1
                    c['boxes'].append(d)
                    c['cx'] = float(np.mean([b[0] + b[2] / 2 for b in c['boxes']]))
                    c['cy'] = float(np.mean([b[1] + b[3] / 2 for b in c['boxes']]))
                    matched = True
                    break
            if not matched:
                clusters.append({'count': 1, 'cx': float(d[0] + d[2] / 2), 'cy': float(d[1] + d[3] / 2), 'boxes': [d]})

        if not clusters:
            return None

        best = max(clusters, key=lambda x: x['count'])
        if best['count'] < 3:
            return None

        med_fx = int(np.median([b[0] for b in best['boxes']]))
        med_fy = int(np.median([b[1] for b in best['boxes']]))
        med_fw = int(np.median([b[2] for b in best['boxes']]))
        med_fh = int(np.median([b[3] for b in best['boxes']]))

        # Expand comfortably around face to encompass facecam frame (face + torso + margins)
        cam_w = int(med_fw * 2.5)
        cam_h = int(med_fh * 2.8)
        cam_x = max(0, min(w - cam_w, med_fx - int(med_fw * 0.75)))
        cam_y = max(0, min(h - cam_h, med_fy - int(med_fh * 0.6)))

        corner = _corner(cam_x, cam_y, cam_x + cam_w, cam_y + cam_h, w, h)
        return {"x": cam_x, "y": cam_y, "w": cam_w, "h": cam_h,
                "corner": corner, "score": 98.0, "conf": "high"}
    except Exception:
        return None


def detect(path: str | Path, ask=None, creator: str = None) -> dict | None:
    """The facecam's box in the source, in source pixels, or None.

    The box is given as x, y, width, height, with the confidence in "score" and
    how sure we are that it is a camera in "conf"."""
    # 1. Fast reliable YuNet neural face detection first
    cv_box = _detect_faces_cv(path)
    if cv_box:
        return cv_box

    # 2. Known creator facecam profile preset - ONLY accepted if verified to contain a real human face!
    if creator:
        c_clean = "".join(c for c in str(creator).lower() if c.isalnum())
        # Check against pure gameplay / review channels (no facecam!)
        if not any(rev in c_clean for rev in ("review", "ign", "gameranx", "breakdown", "trailer", "cinematic")):
            for key, preset in CREATOR_FACECAM_PRESETS.items():
                k_clean = "".join(c for c in key.lower() if c.isalnum())
                if k_clean in c_clean or c_clean in k_clean:
                    w, h = _size(path)
                    if w > 0 and h > 0:
                        rx, ry, rw, rh = preset["rel"]
                        candidate = [int(w * rx), int(h * ry), int(w * rw), int(h * rh)]
                        # CRITICAL QUALITY GATE: Verify that the preset box actually contains a real human face!
                        if verify_face_in_region(path, candidate, min_hits=2):
                            return {
                                "x": candidate[0], "y": candidate[1],
                                "w": candidate[2], "h": candidate[3],
                                "corner": preset["corner"], "score": 95.0, "conf": "high"
                            }

    # 3. Fallback edge and stillness analysis
    frames = _frames(path)
    if len(frames) < 4:
        return None
    w, h = _size(path)
    if not w or not h:
        return None
    still = _stillness(frames)
    light = frames.astype(np.float32).mean(axis=0)
    looked, hinted = (False, None)
    if ask is not None:
        looked, hinted = _asked(path, ask)
        if looked and not hinted:
            return None                    # it looked, and there is no webcam on this stream
    vx, hy = _profiles(frames)
    vpeaks, hpeaks = _peaks(vx, 40), _peaks(hy, 40)
    found = _local(vpeaks, hpeaks, still, light) if (vpeaks and hpeaks) else []
    if looked and hinted:
        match = max(found, key=lambda c: _overlap(c, hinted)) if found else None
        if match and _overlap(match, hinted) >= MATCH:
            return _finish(path, match, w, h, still)
        seen = _seen(path, hinted, w, h, still, light)
        if seen:
            return seen
    if not found:
        return None
    return _finish(path, found[0], w, h, still)

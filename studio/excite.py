"""Excitement and game-event scoring from spoken words (English, Hinglish, and Hindi).

Detects hype reactions ("oh my god", "bhaago", "arre yaar") and gaming events ("wasted", "five stars",
"headshot", "one tap", "clutch", "squad wipe", "booyah") in word-timed transcripts.
"""
import re
import numpy as np

_LEX = [
    (r"oh my (god|gosh)|omg|oh shit|holy (shit|crap|fuck|hell)?|no way|what the (fuck|f|hell)|wtf|oh no+|nooo+|oh fuck|oh god", 3),
    (r"let'?s go+|lets go+|insane|crazy|bruh|yooo+|yoo+|ayo|bro+\b|dude|sheesh|goat|clip (it|that)", 2),
    (r"run|run run|go go|get out|watch out|behind you|help|police|cops?|chase|chasing|wanted|swat|shoot|shot|shooting|gun|kill|killed|dead|die|dying|dies", 2),
    (r"boom|explo\w*|blast|blow|crash\w*|fire|burn\w*|bomb|grenade|rocket|jump|flip\w*|fall\w*|drop\w*|ahh+|aaa+h*|scream\w*", 2),
    (r"are+ yaar|arre+|are bhai|oye+|abe+|bhaag\w*|bhago|bachao|pulis|police wale|maar\w*|gaya|goli\w*|dhamaka|uff+|oh teri|kya baat|zabardast|pagal|mast|jhakaas|hat\s*teri", 2),
    (r"अरे+|भागो|भाग|बचाओ|पुलिस|मार|मर गया|गोली|धमाका|ब्लास्ट|पागल|उफ़|ओए|यार", 2),
]

GAME_EVENTS = [
    (r"wasted|busted|mission (passed|failed|complete)|wanted level|(five|5|six|6) stars?|cops? (are )?coming|heist|bank robbery|getaway", 3),
    (r"headshot|head shot|one tap|ace|clutch|(1|one) (v|vs) (\d|one|two|three|four)|squad wipe|wiped|knocked|eliminated|victory royale|chicken dinner|booyah|winner winner", 3),
    (r"double kill|triple kill|quadra kill|penta kill|multi kill|killstreak|kill streak|last (one|man|zone)|final circle|zone", 2),
    (r"वांटेड|बस्टेड|वेस्टेड|मिशन|हेडशॉट|बूयाह|क्लच", 3),
]

_RX = [(re.compile(p, re.I), w) for p, w in (_LEX + GAME_EVENTS)]
_EVENT_RX = re.compile("|".join(p for p, _ in GAME_EVENTS), re.I)
_WEAK = {"oh", "ooh", "whoa", "woah", "wow", "yo", "holy", "damn", "dang", "ugh", "aah", "ahh", "ah", "bro",
         "brother", "nah", "what", "no", "wait", "stop", "yes", "yeah", "arre", "are", "abe", "oye", "uff",
         "अरे", "ओए", "उफ़", "वाह", "नहीं"}


def _w_text(w: dict) -> str:
    return str(w.get("w") if "w" in w else w.get("text", ""))


def _w_start(w: dict) -> float:
    return float(w.get("s") if "s" in w else w.get("start", 0.0))


def game_events(words: list) -> list:
    """Return up to 5 distinct game event phrases detected in a clip's transcript."""
    text = " ".join(_w_text(w) for w in words or [])
    return sorted({m.group(0).lower() for m in _EVENT_RX.finditer(text)})[:5]


def word_weight(text: str) -> float:
    t = text.strip().lower()
    if not t:
        return 0.0
    w = 0.0
    for rx, wt in _RX:
        m = rx.search(t)
        if rx.fullmatch(t) or (len(t) > 3 and m and m.group(0) == t):
            w = max(w, wt)
    if w == 0 and t.strip(",.!?") in _WEAK:
        w = 0.7
    if t.endswith("!"):
        w += 1.0
    return w


def _phrase_weight(words: list, i: int) -> float:
    best = 0.0
    for n in (3, 2):
        if i + n <= len(words):
            joined = " ".join(_w_text(w).strip(",.!?").lower() for w in words[i:i + n])
            for rx, wt in _RX:
                m = rx.search(joined)
                if m and len(m.group(0)) >= len(joined) - 1:
                    best = max(best, wt)
    return best


def seconds_signal(words: list, duration: float) -> np.ndarray:
    """Return a smoothed 0..1 per-second excitement curve across the transcript."""
    n = max(1, int(np.ceil(duration)))
    sig = np.zeros(n)
    for i, w in enumerate(words or []):
        wt = max(word_weight(_w_text(w)), _phrase_weight(words, i))
        if wt:
            s = min(n - 1, max(0, int(_w_start(w))))
            sig[s] += wt
    sig = np.minimum(sig, 6)
    sm = np.convolve(sig, np.ones(5) / 5, "same")
    peak = max(float(np.percentile(sm[sm > 0], 95)) if (sm > 0).any() else 1.0, 1.0)
    return np.clip(sm / peak, 0, 1)


def window_score(words: list, duration: float) -> float:
    """Return 0..1 exclamation density score for a candidate clip window."""
    if not words or duration <= 0:
        return 0.0
    total = sum(max(word_weight(_w_text(w)), _phrase_weight(words, i)) for i, w in enumerate(words))
    density = total / max(duration / 8.0, 1.0)
    return float(min(1.0, density / 4.0))

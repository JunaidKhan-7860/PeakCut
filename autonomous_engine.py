"""
PeakCut 24/7 Autonomous Engine - Tier 1 Viral GTA 6 Pipeline
============================================================
Rules & Contract:
1. ZERO COPYING: Never rips existing clips or TikToks from others.
   Ingests only RAW uncut live streams, full 4K gameplay VODs, and official broadcasts.
2. 100% TRANSFORMED:
   - Climax Teaser Hook (Flash-forward to the peak moment for 2.2s with 'WAIT FOR IT... 👀')
   - Hook Punch Zoom (+15%) & Retention Progress Bar
   - Word-by-word kinetic animated captions
   - Ducked background audio
   - High-CTR curiosity-gap titles & Tier 1 hashtags (#gta6 #gtarp #gaming #fyp #shorts)
3. ALGORITHM SPACING (Zero Spam):
   - Maximum 3-4 clips per 24 hours
   - Spaced 3.5 to 4 hours apart aligned with US EST peak scroll times
4. TARGET CHANNELS:
   - YouTube: https://studio.youtube.com/channel/UCOnjYjv4eqnOF3tEk6GUw9Q
   - Instagram: https://www.instagram.com/gamingclipkhan/
"""
import datetime
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

# Add project root to path
ROOT = Path("C:/peakcut")
sys.path.insert(0, str(ROOT))

from studio import accounts, brain, config, creators, ctx, jobs, render, rights, uploader
from studio.roles import (
    HeadManager, PlanThinker, ViralIdeaFinder, AlgorithmManager, ChannelReachSpecialist,
    VODScout, StoryArchitect, ProEditor, SoundMaster, CoverArtist, ComplianceOfficer, BountySubmitter
)

# Setup logging
LOG_DIR = ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "autonomous_engine.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AutonomousEngine")

EXPORT_DIR = ROOT / "viral_exports" / "ready_to_post"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = ROOT / "data" / "autonomous_history.json"

# Strict user directive: DO NOT POST, JUST START MAKING
POSTING_ENABLED = False

TIER1_TARGETS = [
    {
        "name": "Raising ThemRight",
        "creator_id": "raising-themright",
        "mandatory_hashtag": "RaisingThemRight",
        "campaign": "Raising ThemRight Podcast (Sponz \u20b98k Pool)",
        "campaign_id": "606aef7a-79c1-4c91-b8d7-f990baed2d99",
        "content_type": "podcast",
        "focus_game": "",
        "official_handles": ["@raisingthemright", "raising themright", "raisingthemright"],
        "channel_url": "https://www.youtube.com/@RaisingThemRight",
        "sources": [
            "https://www.youtube.com/watch?v=MRtF_rBADpQ"
        ],
        "credit_text": "Watch Raising ThemRight on youtube.com/@RaisingThemRight",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": False,
        "chunk_size": 600,
        "range_start": 0,
        "range_end": 2484,
        "primary_keywords": ["why ages 0-5", "brain", "matter", "parenting", "early childhood", "children", "think"],
        "secondary_keywords": ["science", "learning", "growth"],
        "rules": {
            "use_children_not_kids": True,
            "prohibited_words": ["kids", "kid"],
            "replacement_words": {"kids": "children", "kid": "child"}
        }
    },
    {
        "name": "Techno Gamerz",
        "creator_id": "techno-gamerz",
        "mandatory_hashtag": "TechnoGamerz",
        "campaign": "Techno Gamerz GTA 6 Series",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@technogamerzofficial", "techno gamerz", "technogamerzofficial", "ujn1d683ymw2k5l0euvqfkw"],
        "channel_url": "https://www.youtube.com/@TechnoGamerzOfficial",
        "sources": [
            "https://www.youtube.com/@TechnoGamerzOfficial/videos",
            "ytsearch8:@TechnoGamerzOfficial GTA 6 gameplay",
            "ytsearch8:@TechnoGamerzOfficial GTA"
        ],
        "credit_text": "Watch Techno Gamerz on youtube.com/@TechnoGamerzOfficial",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 300,
        "range_end": 2400,
        "primary_keywords": ["gta 6", "vice city", "gta 5", "gta", "gameplay", "supercar", "girlfriend"],
        "secondary_keywords": ["techno gamerz", "episode"]
    },
    {
        "name": "CarryisLive",
        "creator_id": "carryislive",
        "mandatory_hashtag": "CarryisLive",
        "campaign": "CarryisLive GTA 6 Series",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@carryislive", "carryislive", "carryminati", "ucwvy_f2rww012nkyuuc-p4g"],
        "channel_url": "https://www.youtube.com/@CarryisLive",
        "sources": [
            "https://www.youtube.com/@CarryisLive/streams",
            "ytsearch8:@CarryisLive GTA VI",
            "https://www.youtube.com/@CarryisLive/videos"
        ],
        "credit_text": "Watch CarryisLive on youtube.com/@CarryisLive",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 600,
        "range_end": 3600,
        "primary_keywords": ["gta vi", "vice city", "gta 6", "gta", "story", "carryminati"],
        "secondary_keywords": ["live", "stream"]
    },
    {
        "name": "Mythpat",
        "creator_id": "mythpat",
        "mandatory_hashtag": "Mythpat",
        "campaign": "Mythpat GTA 6 Vice City",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@mythpat", "mythpat", "ucv3m5e0c8xww18151475"],
        "channel_url": "https://www.youtube.com/@Mythpat",
        "sources": [
            "https://www.youtube.com/@Mythpat/streams",
            "ytsearch8:@Mythpat GTA 6",
            "https://www.youtube.com/@Mythpat/videos"
        ],
        "credit_text": "Watch Mythpat on youtube.com/@Mythpat",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 300,
        "range_end": 2400,
        "primary_keywords": ["gta 6", "vice city", "supercar", "full map", "mythpat", "live"],
        "secondary_keywords": ["gta", "gameplay"]
    },
    {
        "name": "Casetoo",
        "creator_id": "casetoo",
        "mandatory_hashtag": "Casetoo",
        "campaign": "Casetoo GTA 6 Live",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@casetoo", "casetoo", "casetoo is live", "casetooyt"],
        "channel_url": "https://www.youtube.com/@Casetoo",
        "sources": [
            "ytsearch8:Casetoo is Live GTA 6",
            "ytsearch8:@Casetoo GTA"
        ],
        "credit_text": "Watch Casetoo on youtube.com/@Casetoo",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 300,
        "range_end": 2400,
        "primary_keywords": ["gta 6", "gta vi", "finish", "day", "casetoo", "vice city"],
        "secondary_keywords": ["live", "challenge"]
    },
    {
        "name": "IShowSpeed",
        "creator_id": "ishowspeed",
        "mandatory_hashtag": "IShowSpeed",
        "campaign": "IShowSpeed GTA 6 Playthrough",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@ishowspeed", "ishowspeed", "speed"],
        "channel_url": "https://www.youtube.com/@IShowSpeed",
        "sources": [
            "https://www.youtube.com/@IShowSpeed/streams",
            "ytsearch8:@IShowSpeed GTA 6",
            "ytsearch8:IShowSpeed beating GTA 6"
        ],
        "credit_text": "Watch IShowSpeed on youtube.com/@IShowSpeed",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 600,
        "range_end": 3600,
        "primary_keywords": ["gta 6", "gta vi", "beating", "mission", "final", "speed"],
        "secondary_keywords": ["stream", "live"]
    },
    {
        "name": "AsianJeff",
        "creator_id": "asianjeff",
        "mandatory_hashtag": "AsianJeff",
        "campaign": "$2,500 AsianJeff GTA 6 Campaign",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@realasianjeff", "@moreasianjeff", "asianjeff", "more asianjeff", "uc9s1dvmhcnoysgkq4vvxoeq"],
        "channel_url": "https://www.youtube.com/@realasianjeff",
        "sources": [
            "https://www.youtube.com/@MoreAsianJeff/videos",
            "https://www.youtube.com/@realasianjeff/streams",
            "ytsearch12:@realasianjeff GTA 6",
            "ytsearch10:@MoreAsianJeff GTA 6",
            "https://www.youtube.com/@realasianjeff/videos"
        ],
        "credit_text": "Watch AsianJeff live on youtube.com/@realasianjeff & @MoreAsianJeff",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 600,
        "range_end": 2400,
        "primary_keywords": ["gta 6", "gta vi", "gta", "vice city", "grand theft auto", "early access", "rockstar", "gta rp", "fivem"],
        "secondary_keywords": ["solo", "fncs", "cup"]
    },
    {
        "name": "ohnepixel",
        "creator_id": "ohnepixel",
        "mandatory_hashtag": "ohnepixel",
        "campaign": "ohnepixel GTA 6 Playthrough",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@ohnepixel", "ohnepixel"],
        "channel_url": "https://www.youtube.com/@ohnepixel",
        "sources": [
            "ytsearch8:ohnepixel GTA VI full playthrough live",
            "https://www.youtube.com/@ohnepixel/streams"
        ],
        "credit_text": "Watch ohnepixel on youtube.com/@ohnepixel",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 300,
        "range_end": 2400,
        "primary_keywords": ["gta vi", "gta 6", "playthrough", "live"],
        "secondary_keywords": ["stream"]
    },
    {
        "name": "Total Gaming",
        "creator_id": "total-gaming",
        "mandatory_hashtag": "TotalGaming",
        "campaign": "Total Gaming GTA Highlights",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["@totalgaming093", "total gaming", "totalgaming093", "ucjwsff37q7g4wvdweee9qia"],
        "channel_url": "https://www.youtube.com/@TotalGaming093",
        "sources": [
            "https://www.youtube.com/@TotalGaming093/videos",
            "ytsearch6:@TotalGaming093 GTA"
        ],
        "credit_text": "Watch Total Gaming on youtube.com/@TotalGaming093",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 300,
        "range_end": 1800,
        "primary_keywords": ["gta", "gta 6", "gaming"],
        "secondary_keywords": ["total gaming", "live"]
    },
    {
        "name": "GTA 6 Master Reviews",
        "creator_id": "gta6-reviews",
        "mandatory_hashtag": "GTA6",
        "campaign": "GTA 6 Reviews & Breakdowns",
        "content_type": "gaming",
        "focus_game": "GTA 6",
        "official_handles": ["gameranx", "ign", "the gta assassin", "gamingbolt", "tmartn2"],
        "sources": [
            "ytsearch6:GTA 6 gameplay review breakdown",
            "ytsearch6:GTA 6 before you buy gameranx",
            "ytsearch6:10 CRAZY Gameplay Features of GTA 6 That Will BLOW Your Mind"
        ],
        "credit_text": "Grand Theft Auto VI analysis & review breakdown",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": False,
        "range_start": 60,
        "range_end": 1200,
        "primary_keywords": ["gta 6", "gameplay", "review", "features", "graphics", "vice city", "breakdown", "before you buy"],
        "secondary_keywords": ["rockstar", "trailer"]
    },
    {
        "name": "Kai Cenat",
        "creator_id": "kai-cenat",
        "mandatory_hashtag": "KaiCenat",
        "campaign": "Kai Cenat $10,000 Pool",
        "content_type": "gaming",
        "official_handles": ["@kaicenatlive", "@kaicenat", "kaicenatlive", "kaicenat"],
        "channel_url": "https://www.youtube.com/@KaiCenat",
        "sources": [
            "https://www.youtube.com/@KaiCenatLive/videos",
            "https://www.youtube.com/@KaiCenat/streams"
        ],
        "credit_text": "Watch Kai Cenat on youtube.com/@KaiCenatLive",
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "range_start": 600,
        "range_end": 2400,
        "preferred_keywords": ["gta", "vice city", "beats", "marathon", "trailer"]
    },
    {
        "name": "Dylan Page",
        "creator_id": "dylan-page",
        "mandatory_hashtag": "DylanPage",
        "campaign": "$5,000 Dylan Page GTA VI Marathon",
        "content_type": "gaming",
        "official_handles": ["@dylanpage", "@dylanpageclips", "dylan page"],
        "channel_url": "https://www.youtube.com/@DylanPage",
        "sources": [
            "ytsearch8:Dylan Page GTA 6 live marathon"
        ],
        "min_duration": 300,
        "max_duration": 100000,
        "no_logo": True,
        "live_focus": True,
        "preferred_keywords": ["gta", "marathon", "gaming"]
    }
]

TIER1_HASHTAGS = ["gta6", "gta6live", "vicecity", "gtarp", "gaming", "shorts", "viral", "fyp"]


def load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed_videos": [], "posted_clips": [], "last_post_time": 0.0}


def save_history(hist: dict):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(hist, indent=2), encoding="utf-8")


def get_next_posting_slot(last_post_time: float) -> float:
    """Calculates next posting slot ensuring at least 3.5 hours gap to prevent spam penalty."""
    min_gap = 3.5 * 3600  # 3.5 hours
    now = time.time()
    next_time = max(now, last_post_time + min_gap)
    return next_time


def search_raw_vod(target: dict, history: dict) -> dict:
    """
    Finds raw uncut long-form streams or gameplay VODs directly from official streamer channels.
    Strictly verifies channel identity against target['official_handles'] to eliminate imposters.
    Dominantly prioritizes primary target (e.g. GTA 6) and allows marathon streams to yield multiple slices.
    """
    sources = target.get("sources") or [target.get("query")]
    official_handles = [h.lower() for h in target.get("official_handles", [])]
    seen_ids = set(history.get("processed_videos", []))
    
    primary_keywords = [k.lower() for k in target.get("primary_keywords", target.get("preferred_keywords", ["gta 6", "gta vi", "gta", "vice city"]))]
    secondary_keywords = [k.lower() for k in target.get("secondary_keywords", [])]

    candidates = []

    for src in sources:
        cmd = [
            str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp",
            "--dump-json", "--flat-playlist", "--playlist-end", "25", src
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            if res.returncode != 0:
                logger.warning(f"yt-dlp search error for {target['name']} source {src}: {res.stderr[:200]}")
                continue
            
            for line in res.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    vid = item.get("id")
                    dur = item.get("duration") or 0
                    title = item.get("title", "")
                    is_live = item.get("is_live", False)
                    was_live = item.get("was_live", False)
                    
                    if not vid:
                        continue
                    if not is_live and (dur < target.get("min_duration", 300) or dur > target.get("max_duration", 100000)):
                        continue
                    if "#shorts" in title.lower() or "tiktok" in title.lower():
                        continue

                    # Strict channel / uploader authentication to prevent imposter accounts
                    uploader_id = (item.get("playlist_uploader_id") or item.get("uploader_id") or item.get("channel_id") or "").lower()
                    uploader_name = (item.get("playlist_uploader") or item.get("uploader") or item.get("channel") or "").lower()
                    if official_handles:
                        is_official = any(h in uploader_id or h in uploader_name for h in official_handles)
                        if not is_official:
                            logger.debug(f"Rejecting non-official channel video '{title}' ({vid}): uploader '{uploader_id}' not in {official_handles}")
                            continue

                    url = item.get("url") or f"https://www.youtube.com/watch?v={vid}"
                    title_l = title.lower()

                    is_primary = any(k in title_l for k in primary_keywords)
                    is_secondary = any(k in title_l for k in secondary_keywords)

                    if is_primary:
                        chunk_size = target.get("chunk_size", 1800)
                        # Chunking for long marathon streams or podcast episodes (> chunk_size)
                        if dur > chunk_size + 120:
                            import math
                            num_chunks = max(1, math.ceil(dur / chunk_size))
                            for c_idx in range(num_chunks):
                                chunk_key = f"{vid}_c{c_idx}_{chunk_size}" if chunk_size != 1800 else f"{vid}_c{c_idx}"
                                if chunk_key in seen_ids:
                                    continue
                                r_offset = 0 if target.get("content_type") == "podcast" else 300
                                r_start = c_idx * chunk_size + (0 if c_idx == 0 and target.get("content_type") == "podcast" else r_offset)
                                r_end = min(dur, (c_idx + 1) * chunk_size + r_offset)
                                if r_start >= dur or r_end <= r_start + 60:
                                    continue
                                is_pod = target.get("content_type") == "podcast"
                                candidates.append({
                                    "id": vid, "chunk_id": chunk_key, "title": title, "url": url,
                                    "duration": dur, "target": target, "is_live": is_live, "was_live": was_live,
                                    "range_start": r_start, "range_end": r_end, "is_primary": True,
                                    "priority": (400 - c_idx) if is_pod else (100 + (15 if is_live else 0) - c_idx),
                                    "source_feed": src
                                })
                        else:
                            if vid not in seen_ids:
                                t_start = target.get("range_start", 600)
                                t_end = target.get("range_end", 2400)
                                if dur <= t_start or dur <= 60:
                                    r_start = 0
                                    r_end = max(10, dur)
                                else:
                                    r_start = t_start
                                    r_end = min(dur, max(r_start + 60, t_end))
                                is_pod = target.get("content_type") == "podcast"
                                candidates.append({
                                    "id": vid, "chunk_id": vid, "title": title, "url": url,
                                    "duration": dur, "target": target, "is_live": is_live, "was_live": was_live,
                                    "range_start": r_start, "range_end": r_end,
                                    "is_primary": True,
                                    "priority": 400 if is_pod else (100 + (15 if is_live else 0)),
                                    "source_feed": src
                                })
                    elif is_secondary or not primary_keywords:
                        # Secondary / minimal fallback games (e.g. Fortnite/tournaments)
                        if vid not in seen_ids:
                            t_start = target.get("range_start", 600)
                            t_end = target.get("range_end", 2400)
                            if dur <= t_start or dur <= 60:
                                r_start = 0
                                r_end = max(10, dur)
                            else:
                                r_start = t_start
                                r_end = min(dur, max(r_start + 60, t_end))
                            candidates.append({
                                "id": vid, "chunk_id": vid, "title": title, "url": url,
                                "duration": dur, "target": target, "is_live": is_live, "was_live": was_live,
                                "range_start": r_start, "range_end": r_end,
                                "is_primary": False, "priority": 5 + (2 if is_live else 0), "source_feed": src
                            })
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Error querying {target['name']} source {src}: {e}")

    if not candidates:
        return None

    # STRICT CAMPAIGN / CONTENT FOCUS:
    # Dedicated podcast campaign or GTA 6 stream chunks are permitted. Other games are suppressed.
    primary_cands = [c for c in candidates if c.get("is_primary")]
    if primary_cands:
        candidates = primary_cands
        logger.info(f"Verified Campaign Source Active for {target['name']}: {len(candidates)} chunk(s) available.")
    else:
        logger.info(f"Content Gate: No remaining primary chunks for {target['name']}. Skipping content.")
        return None

    # Sort candidates by priority descending (GTA 6 live/marathons first)
    candidates.sort(key=lambda x: x["priority"], reverse=True)
    selected = candidates[0]
    logger.info(f"Selected VERIFIED official VOD from {target['name']}: '{selected['title']}' [Chunk: {selected.get('chunk_id')}] ({selected['duration']}s, priority={selected['priority']}) - {selected['url']}")
    return selected


def generate_viral_title_and_hook(target: dict, clip: dict, vod_title: str) -> tuple:
    """
    Generates high-CTR curiosity-gap viral title, hook, and context description.
    Uses local Ollama (llama3.2:latest) with strict YouTube Shorts algorithm rules.
    Dynamically adapts between Gaming (rage/clutch/humor) and Podcast (brain/development/parenting).
    Never generates 'Loud moment', 'GTA 6 All', or robotic phrases.
    """
    c_name = target["name"]
    c_type = target.get("content_type", "gaming")
    raw_title = clip.get("title", "").strip()
    raw_hook = clip.get("hook", "").strip()
    raw_desc = clip.get("description", "").strip()
    category = clip.get("category", "fail").lower()

    # Podcast specific Ollama prompt (Sponz Raising ThemRight)
    if c_type == "podcast":
        try:
            import httpx
            prompt = f"""You are an elite YouTube Shorts & Instagram Reels viral education/parenting algorithm specialist.
Create a high-CTR, high-curiosity educational title (max 52 characters) and short retention context for this podcast moment.
Show: Raising ThemRight Podcast
Episode: {vod_title}
Moment Context: {raw_title} - {raw_desc}

Strict Campaign Rules:
1. Focus on early childhood brain development (ages 0-5), cognitive science, and parenting insights.
2. MUST use the word 'children', NEVER use 'kids'.
3. End title with exactly 1 high-impact emoji (🧠, 💡, 👶, 🌟, 🤯).
4. No fear-based or sensational clickbait claims.
5. Output valid JSON: {{"title": "...", "description": "...", "hook": "..."}}
"""
            resp = httpx.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model": "llama3.2:latest", "prompt": prompt, "format": "json", "stream": False},
                timeout=8
            )
            if resp.status_code == 200:
                res_data = json.loads(resp.json().get("response", "{}"))
                ai_title = res_data.get("title", "").strip()
                ai_desc = res_data.get("description", "").strip()
                ai_hook = res_data.get("hook", "").strip()
                if ai_title and len(ai_title) >= 15:
                    ai_title = ProEditor.sanitize_vocabulary(ai_title, target.get("rules", {}))
                    ai_desc = ProEditor.sanitize_vocabulary(ai_desc, target.get("rules", {}))
                    return ai_title, ai_desc or raw_desc, ai_hook or "LISTEN TO THIS 💡"
        except Exception as e:
            logger.debug(f"Ollama podcast title generation note: {e}")

        podcast_templates = [
            "Why 90% Of Brain Development Happens Before Age 5 🧠",
            "The Critical Window In Early Childhood Development 💡",
            "How Everyday Moments Shape Your Child's Brain 👶",
            "What Science Says About Brain Growth Ages 0-5 🧠",
            "The Power Of Positive Engagement For Children 🌟"
        ]
        seed = int(hashlib.md5(f"{raw_title}_{time.time()}".encode()).hexdigest(), 16)
        fallback_title = podcast_templates[seed % len(podcast_templates)]
        fallback_desc = "Discover why the first five years of childhood development shape lifelong learning and resilience."
        return fallback_title, fallback_desc, "LISTEN TO THIS 💡"

    # Gaming specific Ollama prompt
    try:
        import httpx
        prompt = f"""You are an elite YouTube Shorts & Instagram Reels viral gaming algorithm engineer.
Create a high-CTR, curiosity-gap title (max 52 characters) and short retention context for this gaming moment.
Streamer: {c_name}
VOD Context: {vod_title}
Moment Category: {category}
Raw Details: {raw_title} - {raw_desc}

Viral Algorithm Rules:
1. Title MUST create extreme curiosity, disbelief, or humor that forces mobile scrollers to stop.
   Examples of viral formats:
   - "He Thought He Won Until This Happened 💀"
   - "Bro Had No Idea Who He Was Fighting 😭"
   - "The Ending Left The Whole Stream Silent 🤯"
   - "He Really Did This On Live Stream 💀"
   - "Nobody Expected This Ending 😭"
2. End title with exactly 1 high-impact emoji (💀, 😭, 😱, 🔥, 🤯, 😳).
3. STRICT PROHIBITION: NEVER write words like 'campaign', 'bounty', 'pool', 'reward', 'sponz', 'proof', 'reachclipping', or 'loud moment'. Only write authentic streamer reactions, gameplay action, and natural viewer hooks with @{c_name}.
4. Output valid JSON: {{"title": "...", "description": "...", "hook": "..."}}
"""
        resp = httpx.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "llama3.2:latest", "prompt": prompt, "format": "json", "stream": False},
            timeout=8
        )
        if resp.status_code == 200:
            res_data = json.loads(resp.json().get("response", "{}"))
            ai_title = res_data.get("title", "").strip()
            ai_desc = res_data.get("description", "").strip()
            ai_hook = res_data.get("hook", "").strip()
            if ai_title and len(ai_title) >= 15 and "loud moment" not in ai_title.lower() and "campaign" not in ai_title.lower():
                return ai_title, ai_desc or raw_desc, ai_hook or "WAIT FOR IT... 👀"
    except Exception as e:
        logger.debug(f"Ollama viral title generation note: {e}")

    # Proven algorithmic viral templates (Curiosity Gap & Extreme Emotion)
    emojis = ["💀", "😭", "😱", "🤯", "🔥", "😳"]
    seed = int(hashlib.md5(f"{c_name}_{raw_title}_{time.time()}".encode()).hexdigest(), 16)
    chosen_emoji = emojis[seed % len(emojis)]

    templates_by_category = {
        "fail": [
            f"Bro Thought He Survived Until This Happened {chosen_emoji}",
            f"{c_name} Had No Idea What Was Coming {chosen_emoji}",
            f"The Biggest Choke You Will Ever See {chosen_emoji}",
            f"He Tried To Troll But Instantly Regretted It {chosen_emoji}",
            f"His Reaction At The Very End Is Priceless {chosen_emoji}",
        ],
        "clutch": [
            f"Nobody Believed He Could Pull This Off {chosen_emoji}",
            f"The Most Insane Play You Will See Today {chosen_emoji}",
            f"He Just Broke The Entire Game With This {chosen_emoji}",
            f"1 Against The Entire Server And Then THIS {chosen_emoji}",
        ],
        "rage": [
            f"{c_name} Lost His Entire Mind Over This {chosen_emoji}",
            f"Bro Really Smashed His Setup Over A Game {chosen_emoji}",
            f"The Entire Stream Went Dead Silent {chosen_emoji}",
            f"He Was NOT Ready For What Happened Next {chosen_emoji}",
        ],
        "shock": [
            f"Nobody Expected This To Happen Live On Stream {chosen_emoji}",
            f"Watch What Happens At The Very End {chosen_emoji}",
            f"He Had No Idea Who He Was Playing Against {chosen_emoji}",
            f"The Ending Left Everyone Speechless {chosen_emoji}",
        ]
    }
    pool = templates_by_category.get(category, templates_by_category["shock"])
    fallback_title = pool[seed % len(pool)]
    fallback_desc = f"{c_name} experienced the craziest moment live on stream!"
    return fallback_title, fallback_desc, "WAIT FOR IT... 👀"


def build_viral_metadata(target: dict, clip: dict, vod_title: str) -> tuple:
    """Builds high-CTR, retention-optimized titles and clean creator credits without campaign jargon."""
    c_name = target["name"]
    c_type = target.get("content_type", "gaming")
    tag = target.get("mandatory_hashtag", "gta6")
    credit_line = target.get("credit_text", "")

    viral_title, context_desc, viral_hook = generate_viral_title_and_hook(target, clip, vod_title)

    # Podcast specific metadata (Sponz Raising ThemRight)
    if c_type == "podcast":
        safe_desc = ProEditor.sanitize_vocabulary(context_desc, target.get("rules", {}))
        safe_title = ProEditor.sanitize_vocabulary(viral_title, target.get("rules", {}))
        full_title = f"{safe_title} #{tag} #Parenting"
        if len(full_title) > 65:
            avail = 65 - len(tag) - 13
            full_title = f"{safe_title[:avail].rstrip()}... #{tag} #Parenting"

        desc = f"""{safe_desc}

Raising ThemRight explores the breakthrough science of early childhood development, brain architecture, and positive parenting.

👉 Watch the full episode on the Raising ThemRight YouTube channel: https://www.youtube.com/watch?v=MRtF_rBADpQ

#RaisingThemRight #Parenting #EarlyChildhood #BrainDevelopment #ChildDevelopment #ParentingTips #ParentingHacks #Education #Shorts
"""
        tags = ["RaisingThemRight", "Parenting", "EarlyChildhood", "BrainDevelopment", "ChildDevelopment", "ParentingTips", "Shorts", "Education", "Children"]
        return full_title.strip(), desc.strip(), tags

    # Gaming viral metadata
    full_title = f"{viral_title} #{tag} #Shorts"
    if len(full_title) > 65:
        avail = 65 - len(tag) - 11
        full_title = f"{viral_title[:avail].rstrip()}... #{tag} #Shorts"

    desc = f"""{context_desc} Drop a 💀 below if you caught what happened! 👇

Credit: @{c_name}
"""
    if credit_line:
        desc += f"Watch: {credit_line}\n"
    else:
        desc += f"Original Stream: @{c_name}\n"

    desc += f"""
🎮 Follow @gamingclipkhan for daily viral GTA 6 live moments & crazy plays!

#GTA6 #GTA6Live #{tag} #Shorts #Gaming #Viral #FYP #GamingClips #GTA6Gameplay
"""

    tags = ["GTA6", "GTA6Live", tag, c_name, f"@{c_name}", "Gaming", "Shorts", "Viral", "FYP", "GTA6Gameplay", "StreamerMoments"]
    return full_title.strip(), desc.strip(), tags


def process_vod_into_viral_clip(vod: dict, hist: dict):
    """Processes raw VOD with PeakCut: AI moments, climax teaser hook, bouncing captions, and renders."""
    vid = vod["id"]
    title = vod["title"]
    url = vod["url"]
    creator_id = vod["target"].get("creator_id")
    target = vod["target"]
    tag = target.get("mandatory_hashtag", "gta6")
    campaign_name = target.get("campaign", "Campaign Bounty")
    campaign_id = target.get("campaign_id", "")
    
    chunk_id = vod.get("chunk_id", vid)
    HeadManager.update_role_heartbeat("head_manager", "allocating_job", f"Target: {target['name']} ({campaign_name})")
    HeadManager.update_role_heartbeat("plan_thinker", "slate_balanced", f"Ratio target: GTA 6 Dominant | Current: {target['name']}")
    HeadManager.update_role_heartbeat("viral_idea_finder", "trend_scouted", f"Creator: {target['name']} | VOD: {title[:32]}...")
    HeadManager.update_role_heartbeat("vod_scout", "ingesting_vod", f"Verified Source: {title} [{chunk_id}]")
    
    r_start = vod.get("range_start", target.get("range_start", 600))
    r_end = vod.get("range_end", target.get("range_end", 2400))
    vod_dur = vod.get("duration", 0)
    if vod_dur > 0:
        if r_start >= vod_dur:
            r_start = max(0, vod_dur - 600)
        r_end = min(vod_dur, max(r_start + 60, r_end))
    if r_end <= r_start:
        r_start = 0
        r_end = vod_dur if vod_dur > 0 else 600
    logger.info(f"Ingesting raw source VOD for {target['name']}: {title} ({url}) [Range: {r_start}s - {r_end}s | Chunk: {chunk_id}]")
    opts = ProEditor.get_editor_config(target)
    opts["range_start"] = r_start
    opts["range_end"] = r_end
    
    with ctx.as_user("u_local"):
        source = {"type": "url", "url": url, "name": title}
        job = jobs.create(source, opts, enqueue=True, creator=creator_id)
        jid = job["id"]
        logger.info(f"Created PeakCut Job: {jid} for {title}")
        
        # Wait for job to process and render
        max_wait = 1800  # 30 min max for download + transcription + render
        start_wait = time.time()
        while time.time() - start_wait < max_wait:
            j = jobs.get(jid)
            if not j:
                break
            st = j.get("status")
            stage = j.get("stage", "")
            prog = j.get("progress", 0.0)
            logger.info(f"Job {jid} [{st}] - {stage} ({prog*100:.0f}%)")
            HeadManager.update_role_heartbeat("pro_editor", "processing", f"Job {jid} [{stage}] {prog*100:.0f}%")
            
            if st == "done":
                logger.info(f"Job {jid} finished with {len(j.get('clips', []))} clips.")
                clips = [c for c in j.get("clips", []) if c.get("status") == "done"]
                if not clips:
                    logger.warning(f"No clips finished in job {jid}")
                    break
                
                # Pick top clip by score
                best_clip = max(clips, key=lambda c: c.get("score", 0))
                logger.info(f"Selected top viral clip: '{best_clip.get('title')}' (Score: {best_clip.get('score')})")
                
                # Stage to viral_exports
                clip_file = Path(j["dir"]) / "clips" / best_clip["file"]
                cover_file = Path(j["dir"]) / "clips" / best_clip["cover"]
                
                export_id = f"{tag}_{int(time.time())}_{best_clip['id']}"
                dest_mp4 = EXPORT_DIR / f"{export_id}.mp4"
                dest_jpg = EXPORT_DIR / f"{export_id}.jpg"
                
                import shutil
                if clip_file.exists():
                    shutil.copyfile(clip_file, dest_mp4)
                if cover_file.exists():
                    shutil.copyfile(cover_file, dest_jpg)
                
                # Build viral, high-CTR metadata with creator attribution & copyright credit
                clean_title, rich_desc, meta_tags = build_viral_metadata(target, best_clip, title)
                
                has_rights, rights_reason, _ = rights.check_rights(target["name"], campaign_name)
                clip_status = "ready_to_post" if has_rights else "license_needed"

                next_slot = get_next_posting_slot(hist.get("last_post_time", 0.0))
                now_ts = time.time()
                target_slot = next_slot if next_slot > now_ts + 600 else (now_ts + 900)
                publish_at_iso = datetime.datetime.fromtimestamp(target_slot, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

                meta = {
                    "id": export_id,
                    "campaign": campaign_name,
                    "campaign_id": campaign_id,
                    "content_type": target.get("content_type", "gaming"),
                    "target_creator": target["name"],
                    "mandatory_hashtag": f"#{tag}",
                    "title": clean_title,
                    "description": rich_desc,
                    "hashtags": meta_tags,
                    "video_path": str(dest_mp4),
                    "cover_path": str(dest_jpg),
                    "scheduled_for": next_slot,
                    "publish_at": publish_at_iso,
                    "target_channels": {
                        "youtube": "https://studio.youtube.com/channel/UCOnjYjv4eqnOF3tEk6GUw9Q",
                        "instagram": "https://www.instagram.com/gamingclipkhan/"
                    },
                    "status": clip_status,
                    "privacy_status": "private",
                    "rights_verified": has_rights,
                    "rights_notes": rights_reason,
                    "score": best_clip.get("score", 90),
                    "source": title
                }

                # Audit clip via ComplianceOfficer
                is_compliant, audit_errors = ComplianceOfficer.audit_clip(meta, target)
                if not is_compliant:
                    logger.warning(f"Compliance issues detected: {audit_errors}")
                
                meta_file = EXPORT_DIR / f"{export_id}_meta.json"
                meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                logger.info(f"Packaged clip for scheduled posting: {dest_mp4} (Title: {clean_title})")

                # Offload to Cloud CDN & Purge local file to keep PC disk storage clean
                from studio import cloud_storage
                meta = cloud_storage.sync_clip_to_cloud(meta, purge_local=True)
                cloud_storage.purge_raw_job_media(Path(j["dir"]))

                HeadManager.update_role_heartbeat("story_architect", "hook_crafted", f"Hook Title: '{clean_title[:32]}...'")
                HeadManager.update_role_heartbeat("algorithm_manager", "retention_modeled", "Whoosh SFX t=0.05s, APV target >90%, auto-ducking")
                HeadManager.update_role_heartbeat("channel_reach_specialist", "audience_optimized", f"Tags: #{tag} | Mobile Feed Optimized")
                HeadManager.update_role_heartbeat("sound_master", "audio_mastered", "EBU R128 (-14 LUFS) & Sidechain Ducking Active")
                HeadManager.update_role_heartbeat("cover_artist", "poster_rendered", f"Cover Art: {dest_jpg.name}")
                HeadManager.update_role_heartbeat("compliance_officer", "audited", f"Clip {export_id} audited: Compliant={is_compliant}")
                HeadManager.update_role_heartbeat("bounty_submitter", "scheduled", f"Queued for {publish_at_iso} (YouTube publishAt)")

                # Update history
                hist.setdefault("processed_videos", []).append(chunk_id)
                hist.setdefault("staged_clips", []).append(meta)
                save_history(hist)
                return meta
                
            elif st == "error":
                logger.error(f"Job {jid} failed: {j.get('error')}")
                break
                
            time.sleep(15)
            
    hist.setdefault("processed_videos", []).append(chunk_id)
    save_history(hist)
    return None


def clean_stale_cache(max_age_hours: float = 12.0) -> float:
    """
    Safely prunes stale raw source VODs and orphaned .part downloads older than max_age_hours.
    Strictly preserves viral_exports/ready_to_post/ and lightweight metadata JSONs.
    Returns MB reclaimed.
    """
    users_dir = config.USERS_DIR
    now = time.time()
    reclaimed_bytes = 0
    cleaned_count = 0

    try:
        if users_dir.exists():
            for root, dirs, files in os.walk(users_dir):
                for f in files:
                    p = Path(root) / f
                    try:
                        mtime = p.stat().st_mtime
                        size = p.stat().st_size
                        # 1. Orphaned incomplete downloads older than 2 hours
                        if f.endswith(('.part', '.ytdl', '.tmp')) and (now - mtime > 7200):
                            p.unlink(missing_ok=True)
                            reclaimed_bytes += size
                            cleaned_count += 1
                        # 2. Large raw source VODs in jobs older than max_age_hours
                        elif f in ('source.mp4', 'audio_src.m4a', 'source.wav', 'audio.m4a') and (now - mtime > max_age_hours * 3600):
                            p.unlink(missing_ok=True)
                            reclaimed_bytes += size
                            cleaned_count += 1
                    except Exception:
                        pass
        if cleaned_count > 0:
            mb = reclaimed_bytes / (1024 * 1024)
            logger.info(f"Storage Optimizer: Reclaimed {mb:.2f} MB across {cleaned_count} stale raw files.")
            return mb
    except Exception as e:
        logger.warning(f"Storage cleaner notice: {e}")

    try:
        from studio import cloud_storage
        cloud_storage.purge_all_raw_vods()
    except Exception:
        pass

    return 0.0


def discover_live_gta6_stream(hist: dict) -> dict:
    """
    Dynamic Live Radar: Actively discovers live GTA 6 streams and recent marathon broadcasts.
    Scans live query feeds across India and global top creators:
    - ytsearch10:GTA 6 live stream India
    - ytsearch10:GTA 6 gameplay live
    - ytsearch10:GTA VI marathon live
    Prioritizes active live broadcasts (is_live=True) and marathon streams from verified creators.
    """
    seen_ids = set(hist.get("processed_videos", []))
    radar_feeds = [
        "ytsearch10:GTA 6 live stream India",
        "ytsearch10:GTA 6 gameplay live",
        "ytsearch10:GTA VI marathon live"
    ]
    candidates = []

    for feed in radar_feeds:
        cmd = [
            str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp",
            "--dump-json", "--flat-playlist", "--playlist-end", "10", feed
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
            if res.returncode != 0:
                continue
            for line in res.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    vid = item.get("id")
                    dur = item.get("duration") or 0
                    title = item.get("title", "")
                    uploader = item.get("uploader") or item.get("channel") or ""
                    is_live = item.get("is_live", False)
                    was_live = item.get("was_live", False)

                    if not vid or dur < 300:
                        continue
                    if "#shorts" in title.lower() or "tiktok" in title.lower():
                        continue

                    # Match against verified creators
                    matched_target = None
                    for t in TIER1_TARGETS:
                        handles = [h.lower() for h in t.get("official_handles", [])] + [t["name"].lower()]
                        if any(h in uploader.lower() for h in handles):
                            matched_target = t
                            break

                    if not matched_target:
                        # Check rights check directly
                        has_r, _, _ = rights.check_rights(uploader, f"{uploader} GTA 6 Highlights")
                        if has_r:
                            matched_target = {
                                "name": uploader,
                                "creator_id": re.sub(r'[^a-zA-Z0-9]', '-', uploader).lower(),
                                "mandatory_hashtag": re.sub(r'[^a-zA-Z0-9]', '', uploader),
                                "campaign": f"{uploader} GTA 6 Stream",
                                "content_type": "gaming",
                                "focus_game": "GTA 6",
                                "credit_text": f"Watch {uploader} live on YouTube",
                                "range_start": 300,
                                "range_end": 2400,
                                "live_focus": True
                            }

                    if not matched_target:
                        continue

                    url = item.get("url") or f"https://www.youtube.com/watch?v={vid}"

                    # Chunk if long marathon (> 40 min)
                    if dur > 2400:
                        chunk_size = 1800
                        num_chunks = max(1, int(dur // chunk_size))
                        for c_idx in range(num_chunks):
                            chunk_key = f"{vid}_c{c_idx}"
                            if chunk_key in seen_ids:
                                continue
                            r_start = c_idx * 1800 + 300
                            r_end = min(dur, (c_idx + 1) * 1800 + 300)
                            candidates.append({
                                "id": vid, "chunk_id": chunk_key, "title": title, "url": url,
                                "duration": dur, "target": matched_target, "is_live": is_live, "was_live": was_live,
                                "range_start": r_start, "range_end": r_end, "is_primary": True,
                                "priority": 200 + (30 if is_live else 0) - c_idx, "source_feed": feed
                            })
                    else:
                        if vid not in seen_ids:
                            candidates.append({
                                "id": vid, "chunk_id": vid, "title": title, "url": url,
                                "duration": dur, "target": matched_target, "is_live": is_live, "was_live": was_live,
                                "range_start": matched_target.get("range_start", 300),
                                "range_end": min(dur, matched_target.get("range_end", 2400)),
                                "is_primary": True, "priority": 150 + (30 if is_live else 0), "source_feed": feed
                            })
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Live radar feed note: {e}")

    if not candidates:
        return None

    candidates.sort(key=lambda x: x["priority"], reverse=True)
    selected = candidates[0]
    logger.info(f"🎯 LIVE GTA 6 RADAR DETECTED: '{selected['title']}' by {selected['target']['name']} (Live={selected['is_live']}, Duration={selected['duration']}s, Chunk={selected.get('chunk_id')})")
    return selected


def run_cycle():
    """Single autonomous cycle: check schedule, find fresh raw stream, create original clip, stage post."""
    hist = load_history()
    last_post = hist.get("last_post_time", 0.0)
    now = time.time()
    
    logger.info("=== Running Autonomous Viral Cycle ===")
    logger.info(f"Last post time: {datetime.datetime.fromtimestamp(last_post) if last_post else 'None'}")
    
    # 0. Storage optimization & disk cleanup
    clean_stale_cache(12.0)

    # 1. Log separated platform & queue audit
    try:
        summary_data = uploader.get_status_summary()
        sm = summary_data["summary"]
        logger.info(
            f"Platform Status Audit: Public={sm['public_count']} | "
            f"Private/Draft={sm['private_draft_count']} | "
            f"Queued(LicenseNeeded)={sm['queued_license_needed_count']} | "
            f"Queued(Ready)={sm['queued_ready_count']} | "
            f"FailedAttempts={sm['failed_count']}"
        )
    except Exception as es:
        logger.warning(f"Could not log status audit: {es}")
    
    # 1. Posting check (strictly bypassed per user directive: "do not post just start making")
    if POSTING_ENABLED:
        try:
            import auto_poster
            auto_poster.post_next_due()
        except Exception as ep:
            logger.error(f"AutoPoster check error: {ep}")
    else:
        logger.info("Posting is strictly FROZEN (Directive: 'do not post just start making'). Pure clipping & rendering mode active.")

    # 2. PRIORITY 1: Targeted Campaign Creators & Official Channels
    for target in TIER1_TARGETS:
        has_rights, rights_reason, _ = rights.check_rights(target["name"], target.get("campaign", ""))
        logger.info(f"Checking target creator: {target['name']} (Verified Rights: {has_rights})")
        vod = search_raw_vod(target, hist)
        if vod:
            logger.info(f"Selected fresh raw VOD from {target['name']}: {vod['title']}")
            clip_meta = process_vod_into_viral_clip(vod, hist)
            if clip_meta:
                logger.info(f"Successfully generated 100% original clip: {clip_meta['title']}")
                if POSTING_ENABLED:
                    try:
                        auto_poster.post_next_due()
                    except Exception:
                        pass
                return
        time.sleep(5)

    # 3. PRIORITY 2: Dynamic Live GTA 6 Radar Check (Secondary Fallback)
    try:
        live_vod = discover_live_gta6_stream(hist)
        if live_vod:
            logger.info(f"Dynamic Radar prioritizing live GTA 6 stream: '{live_vod['title']}' by {live_vod['target']['name']}")
            clip_meta = process_vod_into_viral_clip(live_vod, hist)
            if clip_meta:
                logger.info(f"Successfully generated 100% original clip from live stream: {clip_meta['title']}")
                if POSTING_ENABLED:
                    try:
                        auto_poster.post_next_due()
                    except Exception:
                        pass
                return
    except Exception as er:
        logger.error(f"Dynamic Live Radar scan error: {er}")
    
    # 4. Final check after new clips are staged
    if POSTING_ENABLED:
        try:
            auto_poster.post_next_due()
        except Exception as ep:
            logger.error(f"AutoPoster post-cycle check error: {ep}")
    
    logger.info("Cycle complete. Waiting for next window.")


def main():
    logger.info("Starting PeakCut 24/7 Autonomous Viral Machine...")
    logger.info("Target YouTube: https://studio.youtube.com/channel/UCOnjYjv4eqnOF3tEk6GUw9Q")
    logger.info("Target Instagram: https://www.instagram.com/gamingclipkhan/")
    logger.info("Tier 1 Audience Strategy: Spaced Cadence (3-4h), Climax Teaser Hook, High-CTR Titles")
    
    # Initialize PeakCut job workers and background processors
    logger.info("Initializing PeakCut job worker threads...")
    jobs.start()
    logger.info("Job workers active. Beginning autonomous cycle loop.")

    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"Unexpected error in cycle: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Sleep 2 minutes between scan cycles to keep harvesting fresh campaign moments
        logger.info("Sleeping 2 minutes before next campaign discovery scan...")
        time.sleep(120)


if __name__ == "__main__":
    main()

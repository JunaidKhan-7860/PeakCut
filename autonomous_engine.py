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

TIER1_TARGETS = [
    {
        "name": "Kai Cenat",
        "query": "ytsearch5:Kai Cenat GTA 6 marathon full stream",
        "creator_id": "kai-cenat",
        "mandatory_hashtag": "KaiCenat",
        "campaign": "Kai Cenat $10,000 Pool",
        "min_duration": 300,
        "max_duration": 25000,
        "no_logo": True
    },
    {
        "name": "AsianJeff",
        "query": "ytsearch5:AsianJeff GTA 6 playthrough stream",
        "creator_id": "asianjeff",
        "mandatory_hashtag": "AsianJeff",
        "campaign": "$2,500 AsianJeff Campaign",
        "min_duration": 300,
        "max_duration": 25000,
        "no_logo": True
    },
    {
        "name": "Dasgasd3m",
        "query": "ytsearch5:dasgasd3m GTA 6 kick stream",
        "creator_id": "dasgasd3m",
        "mandatory_hashtag": "dasgasdom3",
        "credit_text": "Watch Dom live on kick.com/dasgasd3m",
        "campaign": "Dasgasd3m x RUCKUS $1K",
        "min_duration": 300,
        "max_duration": 25000,
        "no_logo": False
    },
    {
        "name": "Dylan Page",
        "query": "ytsearch4:Dylan Page GTA 6 marathon",
        "creator_id": "dylan-page",
        "mandatory_hashtag": "DylanPage",
        "campaign": "$5,000 Dylan Page GTA VI Marathon",
        "min_duration": 300,
        "max_duration": 25000,
        "no_logo": True
    },
    {
        "name": "Lauren Hamden",
        "query": "ytsearch3:Lauren Hamden GTA 6 marathon",
        "creator_id": "lauren-hamden",
        "mandatory_hashtag": "LaurenHamden",
        "campaign": "$5,000 Lauren Hamden GTA Marathon",
        "min_duration": 300,
        "max_duration": 25000,
        "no_logo": True
    }
]

TIER1_HASHTAGS = ["gta6", "gtarp", "gta6trailer", "gaming", "fyp", "shorts", "viral"]


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
    """Finds raw uncut long-form streams or gameplay VODs. Never existing shorts."""
    cmd = [
        str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp",
        "--dump-json", "--flat-playlist", target["query"]
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if res.returncode != 0:
            logger.warning(f"yt-dlp search error for {target['name']}: {res.stderr[:200]}")
            return None
        
        seen_ids = set(history.get("processed_videos", []))
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                vid = item.get("id")
                dur = item.get("duration") or 0
                title = item.get("title", "")
                
                # Filter: Never take someone else's short (duration < 120s or '#shorts' in title)
                if vid in seen_ids:
                    continue
                if dur < target["min_duration"] or dur > target["max_duration"]:
                    continue
                if "#shorts" in title.lower() or "tiktok" in title.lower():
                    continue
                
                url = item.get("url") or f"https://www.youtube.com/watch?v={vid}"
                logger.info(f"Found raw source VOD: '{title}' ({dur}s) - {url}")
                return {"id": vid, "title": title, "url": url, "duration": dur, "target": target}
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Error querying {target['name']}: {e}")
    return None


def build_viral_metadata(target: dict, clip: dict, vod_title: str) -> tuple:
    """Builds high-CTR, retention-optimized titles and copyright-safe descriptions with creator credits."""
    c_name = target["name"]
    tag = target.get("mandatory_hashtag", "gta6")
    campaign = target.get("campaign", "")
    credit_line = target.get("credit_text", "")
    hook = clip.get("title") or clip.get("hook") or f"{c_name} Moment"

    emojis = ["💀", "😱", "🔥", "😭", "👀", "💥"]
    chosen_emoji = emojis[int(time.time()) % len(emojis)]

    if not any(e in hook for e in emojis):
        hook = f"{hook} {chosen_emoji}"

    title = f"{hook} #{tag} #Shorts"
    if len(title) > 68:
        title = f"{hook[:68 - len(tag) - 12]}... #{tag} #Shorts"

    desc = f"""{clip.get('description', hook)} Drop a comment below if you saw that coming! 👇

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ORIGINAL CREATOR ATTRIBUTION:
• Original Creator: @{c_name}
• Stream / Highlight: {vod_title}
• Official Campaign: {campaign}
"""
    if credit_line:
        desc += f"• Creator Link: {credit_line}\n"
    else:
        desc += f"• Support the creator: Check out @{c_name}'s official streams!\n"

    desc += f"""
All rights and copyright belong to @{c_name} and original creators. Featured under authorized campaign guidelines.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎮 Channel: Gamingclip (@gamingclip-f1l)
Subscribe for daily viral gaming moments, streamer reactions, and best plays!

#{tag} #Shorts #Gaming #GTA6 #Viral #FYP #StreamerMoments #GamingClips
"""

    tags = [tag, c_name, f"@{c_name}", "Gaming", "Shorts", "Viral", "FYP", "GTA6", "GamingClips", "StreamerMoments"]
    return title.strip(), desc.strip(), tags


def process_vod_into_viral_clip(vod: dict, hist: dict):
    """Processes raw VOD with PeakCut: AI moments, climax teaser hook, bouncing captions, and renders."""
    vid = vod["id"]
    title = vod["title"]
    url = vod["url"]
    creator_id = vod["target"].get("creator_id")
    
    target = vod["target"]
    no_logo = target.get("no_logo", True)
    tag = target.get("mandatory_hashtag", "gta6")
    campaign_name = target.get("campaign", "GTA 6 Bounty")
    credit_line = target.get("credit_text", "")
    
    logger.info(f"Ingesting raw VOD for campaign [{campaign_name}]: {title} ({url})")
    opts = {
        "max_clips": 3,
        "min_len": 22,
        "max_len": 55,
        "range_start": 0,
        "range_end": 720,
        "style": "bounce",
        "layout": "crop",
        "captions": True,
        "music": "auto",
        "music_vol": 0.16,
        "punch_zoom": True,
        "progress_bar": True,
        "teaser_hook": True,
        "teaser_dur": 2.2,
        "teaser_text": "WAIT FOR IT... 👀",
        "corner_tag": "" if no_logo else f"🔴 {target['name']}"
    }
    
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
                
                meta = {
                    "id": export_id,
                    "campaign": campaign_name,
                    "target_creator": target["name"],
                    "mandatory_hashtag": f"#{tag}",
                    "title": clean_title,
                    "description": rich_desc,
                    "hashtags": meta_tags,
                    "video_path": str(dest_mp4),
                    "cover_path": str(dest_jpg),
                    "scheduled_for": get_next_posting_slot(hist.get("last_post_time", 0.0)),
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
                
                meta_file = EXPORT_DIR / f"{export_id}_meta.json"
                meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                logger.info(f"Packaged campaign clip for posting: {dest_mp4} (Campaign: {campaign_name})")
                
                # Update history
                hist.setdefault("processed_videos", []).append(vid)
                hist.setdefault("staged_clips", []).append(meta)
                save_history(hist)
                return meta
                save_history(hist)
                return meta
                
            elif st == "error":
                logger.error(f"Job {jid} failed: {j.get('error')}")
                break
                
            time.sleep(15)
            
    hist.setdefault("processed_videos", []).append(vid)
    save_history(hist)
    return None


def run_cycle():
    """Single autonomous cycle: check schedule, find fresh raw stream, create original clip, stage post."""
    hist = load_history()
    last_post = hist.get("last_post_time", 0.0)
    now = time.time()
    
    logger.info("=== Running Autonomous Viral Cycle ===")
    logger.info(f"Last post time: {datetime.datetime.fromtimestamp(last_post) if last_post else 'None'}")
    
    # 0. Log separated platform & queue audit
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
    
    # 1. Check if any staged clip is due for auto-posting
    try:
        import auto_poster
        auto_poster.post_next_due()
    except Exception as ep:
        logger.error(f"AutoPoster check error: {ep}")

    # 2. Search targets and generate fresh clips ONLY if rights are documented
    for target in TIER1_TARGETS:
        has_rights, rights_reason, _ = rights.check_rights(target["name"], target.get("campaign", ""))
        if not has_rights:
            logger.info(f"Skipping VOD clipping for '{target['name']}': No documented license on file. Enforcing rights gate.")
            continue

        logger.info(f"Checking target creator with verified rights: {target['name']}")
        vod = search_raw_vod(target, hist)
        if vod:
            logger.info(f"Selected fresh raw VOD from {target['name']}: {vod['title']}")
            clip_meta = process_vod_into_viral_clip(vod, hist)
            if clip_meta:
                logger.info(f"Successfully generated 100% original clip: {clip_meta['title']}")
                break
        time.sleep(5)
    
    # 3. Check again after new clips are staged
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

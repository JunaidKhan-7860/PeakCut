"""
PeakCut Organic Growth & Audience Analytics Engine
=================================================
Performs organic growth research, channel audit, and competitor benchmarking:
1. Own Channel Analytics: Views, retention factors, posting patterns, engagement.
2. Instagram Creator Analytics: Meta Graph API insights, media performance.
3. Tier 1 Creator Benchmarking: Public metrics, hooks, pacing, viral formats.
4. Optimal Audience Timing: US / English-speaking peak scroll windows.
5. Content Rights Audit: Strictly keeps unlicensed content blocked.
"""
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path("C:/peakcut")
sys.path.insert(0, str(ROOT))

from studio import uploader, rights

logging.basicConfig(level=logging.INFO, format="%(asctime)s [GROWTH] %(levelname)s - %(message)s")
logger = logging.getLogger("PeakCutGrowth")


def analyze_youtube_channel() -> Dict[str, Any]:
    """Analyzes authenticated YouTube channel using official YouTube Data API v3."""
    from googleapiclient.discovery import build

    creds = uploader.get_youtube_credentials()
    if not creds:
        return {"error": "YouTube credentials not available"}

    try:
        yt = build("youtube", "v3", credentials=creds)
        ch_res = yt.channels().list(mine=True, part="snippet,contentDetails,statistics").execute()
        items = ch_res.get("items", [])
        if not items:
            return {"error": "No channel found for authenticated account"}

        ch = items[0]
        stats = ch.get("statistics", {})
        snip = ch.get("snippet", {})
        cd = ch.get("contentDetails", {})
        uploads_id = cd.get("relatedPlaylists", {}).get("uploads")

        # Fetch recent uploads
        videos = []
        if uploads_id:
            pl_res = yt.playlistItems().list(
                playlistId=uploads_id,
                part="snippet,contentDetails",
                maxResults=25
            ).execute()
            vid_ids = [v["contentDetails"]["videoId"] for v in pl_res.get("items", [])]
            if vid_ids:
                v_res = yt.videos().list(
                    id=",".join(vid_ids),
                    part="snippet,statistics,contentDetails,status"
                ).execute()
                for v in v_res.get("items", []):
                    v_snip = v.get("snippet", {})
                    v_stats = v.get("statistics", {})
                    v_stat = v.get("status", {})
                    v_cd = v.get("contentDetails", {})
                    videos.append({
                        "id": v.get("id"),
                        "title": v_snip.get("title"),
                        "published_at": v_snip.get("publishedAt"),
                        "privacy": v_stat.get("privacyStatus"),
                        "views": int(v_stats.get("viewCount", 0)),
                        "likes": int(v_stats.get("likeCount", 0)),
                        "comments": int(v_stats.get("commentCount", 0)),
                        "duration": v_cd.get("duration"),
                        "tags": v_snip.get("tags", [])
                    })

        public_videos = [v for v in videos if v["privacy"] == "public"]
        total_views = int(stats.get("viewCount", 0))
        sub_count = int(stats.get("subscriberCount", 0))
        vid_count = int(stats.get("videoCount", 0))

        return {
            "channel_title": snip.get("title"),
            "custom_url": snip.get("customUrl"),
            "published_at": snip.get("publishedAt"),
            "subscribers": sub_count,
            "total_views": total_views,
            "total_videos": vid_count,
            "recent_videos": videos,
            "public_videos_count": len(public_videos),
            "avg_views_per_public_video": (total_views / max(1, len(public_videos))) if public_videos else 0
        }
    except Exception as e:
        logger.error(f"Error analyzing YouTube channel: {e}")
        return {"error": str(e)}


def analyze_instagram_account() -> Dict[str, Any]:
    """Analyzes authenticated Instagram account via Meta Graph API."""
    import httpx

    creds_file = ROOT / "config" / "credentials" / "instagram_credentials.json"
    if not creds_file.exists():
        return {"error": "Instagram credentials missing"}

    try:
        creds = json.loads(creds_file.read_text(encoding="utf-8"))
        token = creds.get("access_token")
        ig_user_id = creds.get("ig_user_id")

        if not token or not ig_user_id or not str(ig_user_id).isdigit():
            return {"error": "Invalid or non-numeric Instagram credentials"}

        # 1. Profile information
        url_user = f"https://graph.facebook.com/v21.0/{ig_user_id}"
        r_user = httpx.get(
            url_user,
            params={"fields": "id,username,name,media_count,followers_count,follows_count", "access_token": token},
            timeout=20
        )
        if r_user.status_code != 200:
            return {"error": f"Graph API returned HTTP {r_user.status_code}: {r_user.text}"}
        user_data = r_user.json()

        # 2. Media / Reels list
        url_media = f"https://graph.facebook.com/v21.0/{ig_user_id}/media"
        r_media = httpx.get(
            url_media,
            params={
                "fields": "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count",
                "limit": 15,
                "access_token": token
            },
            timeout=20
        )
        media_items = r_media.json().get("data", []) if r_media.status_code == 200 else []

        # 3. Insights
        insights = {}
        try:
            url_ins = f"https://graph.facebook.com/v21.0/{ig_user_id}/insights"
            r_ins = httpx.get(
                url_ins,
                params={
                    "metric": "reach,impressions,total_interactions",
                    "metric_type": "total_value",
                    "period": "day",
                    "access_token": token
                },
                timeout=20
            )
            if r_ins.status_code == 200:
                for item in r_ins.json().get("data", []):
                    insights[item.get("name")] = item.get("total_value", {}).get("value", 0)
        except Exception:
            pass

        return {
            "username": user_data.get("username"),
            "name": user_data.get("name"),
            "followers": user_data.get("followers_count", 0),
            "following": user_data.get("follows_count", 0),
            "media_count": user_data.get("media_count", 0),
            "recent_media": media_items,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error analyzing Instagram account: {e}")
        return {"error": str(e)}


def benchmark_tier1_creators() -> Dict[str, Any]:
    """
    Public metrics and viral architecture benchmarking for Tier 1 creators:
    Kai Cenat, AsianJeff, Dasgasd3m, Dylan Page.
    """
    benchmarks = {
        "Kai Cenat": {
            "platform_focus": ["Twitch", "YouTube", "TikTok"],
            "core_appeal": "High-intensity physical comedy, dramatic reactions, marathon endurance, loud audio peaks.",
            "hook_types": [
                "Direct shock statement in first 1.5 seconds ('WHAT DID HE JUST SAY?!')",
                "Rapid facecam zoom on sudden jump-scare or NPC collision",
                "Teaser flash-forward (2s snippet of the climax, then rewinding)"
            ],
            "optimal_pacing": "Fast cut cadence: cut every 1.8 - 2.5 seconds. Retain high-energy audio throughout.",
            "top_hashtags": ["#KaiCenat", "#gta6", "#gaming", "#fyp", "#twitchclips", "#viral"],
            "campaign_requirements": "Source strictly from GTA 6 marathon; Kai must be the main focus; hashtag #KaiCenat."
        },
        "AsianJeff": {
            "platform_focus": ["YouTube", "Twitch", "TikTok"],
            "core_appeal": "High-speed gameplay trash talk, unexpected fails, comedic rage, banter with chat.",
            "hook_types": [
                "Immediate dilemma: 'He had 5 seconds to escape this...'",
                "Banter hook: 'Bro thought he was safe until...' with word-by-word highlighted captions",
                "Score counter or challenge hook"
            ],
            "optimal_pacing": "Punchy 20 - 32 second format. Punch-zoom on vocal inflections.",
            "top_hashtags": ["#AsianJeff", "#gta6", "#gtarp", "#gaming", "#shorts", "#fyp"],
            "campaign_requirements": "Source strictly from Nov 19+ GTA 6 streams; AsianJeff main focus; #AsianJeff; non-negative; NO logos."
        },
        "Dasgasd3m (Dom)": {
            "platform_focus": ["Kick", "TikTok", "YouTube Shorts"],
            "core_appeal": "Unexpected glitches, comedic NPC dialogues, story twists, expressive facecam reactions.",
            "hook_types": [
                "Glitch discovery: 'Dom found the craziest glitch in GTA 6...'",
                "Story reaction: 'His reaction to this mission fail is unhinged 💀'",
                "Chat exchange: 'Chat baited him into doing this...'"
            ],
            "optimal_pacing": "22 - 40 seconds. Let the setup breathe (3s), punch the reaction (10s), payoff (final 5s).",
            "top_hashtags": ["#dasgasdom3", "#kickstreaming", "#gta6", "#gaming", "#viral"],
            "campaign_requirements": "Nov 18+ streams; #dasgasdom3; credit 'Watch Dom live on kick.com/dasgasd3m'; submit within 30 min of post."
        },
        "Dylan Page": {
            "platform_focus": ["TikTok", "YouTube Shorts"],
            "core_appeal": "High-retention storytelling, curiosity gap hooks, observational gaming humor.",
            "hook_types": [
                "Curiosity statement: 'Nobody noticed this detail in GTA 6 until now...'",
                "Micro-story structure: Hook -> Suspense -> Twist payoff",
                "Clean sound design with ducked ambient music"
            ],
            "optimal_pacing": "30 - 45 seconds. Clear narrative flow with bold subtitle highlights.",
            "top_hashtags": ["#DylanPage", "#GTA6", "#gaming", "#shorts", "#trending"],
            "campaign_requirements": "Sourced from GTA 6 marathon; Dylan Page as main focus; #DylanPage."
        }
    }

    posting_windows_us = [
        {"window": "Morning Commute", "time_est": "7:30 AM - 9:00 AM EST", "time_utc": "12:30 PM - 2:00 PM UTC", "engagement_type": "Quick scroll / discovery"},
        {"window": "Lunch Peak", "time_est": "12:00 PM - 1:30 PM EST", "time_utc": "5:00 PM - 6:30 PM UTC", "engagement_type": "High watch-time / Shorts feed"},
        {"window": "After School / Work", "time_est": "4:30 PM - 6:00 PM EST", "time_utc": "9:30 PM - 11:00 PM UTC", "engagement_type": "Viral wave initiation"},
        {"window": "Prime Evening Scroll", "time_est": "8:00 PM - 10:30 PM EST", "time_utc": "1:00 AM - 3:30 AM UTC", "engagement_type": "Maximum comment & share volume"}
    ]

    return {
        "tier1_competitors": benchmarks,
        "optimal_posting_windows_us_est": posting_windows_us
    }


def audit_content_rights() -> Dict[str, Any]:
    """Audits the local licenses database and staging directory for permission status."""
    licenses = rights.load_licenses()
    verified_creators = licenses.get("verified_creators", {})
    campaign_agreements = licenses.get("campaign_agreements", {})

    export_dir = ROOT / "viral_exports" / "ready_to_post"
    staged_meta = list(export_dir.glob("*_meta.json")) if export_dir.exists() else []

    blocked_clips = []
    approved_clips = []

    for mf in staged_meta:
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            cid = m.get("id")
            creator = m.get("target_creator") or m.get("creator", "Unknown")
            campaign = m.get("campaign", "")
            has_rights, reason, lic = rights.check_rights(creator, campaign)
            if has_rights:
                approved_clips.append({"id": cid, "creator": creator, "license": lic.get("license_id")})
            else:
                blocked_clips.append({"id": cid, "creator": creator, "reason": reason})
        except Exception:
            pass

    return {
        "verified_licenses_count": len(verified_creators),
        "verified_creators": verified_creators,
        "campaign_agreements": campaign_agreements,
        "total_staged_clips": len(staged_meta),
        "blocked_clips_count": len(blocked_clips),
        "approved_clips_count": len(approved_clips),
        "blocked_clips": blocked_clips,
        "approved_clips": approved_clips
    }


def run_full_organic_audit() -> Dict[str, Any]:
    """Executes full analytics and benchmarking suite."""
    logger.info("Executing comprehensive organic growth audit...")
    yt_data = analyze_youtube_channel()
    ig_data = analyze_instagram_account()
    comp_data = benchmark_tier1_creators()
    rights_data = audit_content_rights()

    report = {
        "timestamp": time.time(),
        "youtube_channel": yt_data,
        "instagram_account": ig_data,
        "competitor_benchmarks": comp_data["tier1_competitors"],
        "posting_windows": comp_data["optimal_posting_windows_us_est"],
        "rights_audit": rights_data
    }

    report_file = ROOT / "data" / "organic_growth_audit.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info(f"Organic growth audit completed and saved to {report_file}")
    return report


if __name__ == "__main__":
    report = run_full_organic_audit()
    print("\n" + "=" * 65)
    print("      PEAKCUT ORGANIC GROWTH & AUDIENCE AUDIT REPORT")
    print("=" * 65)
    print(f"\n[1] YouTube Channel: {report['youtube_channel'].get('channel_title')} ({report['youtube_channel'].get('custom_url')})")
    print(f"  • Subscribers: {report['youtube_channel'].get('subscribers')}")
    print(f"  • Total Views: {report['youtube_channel'].get('total_views')}")
    print(f"  • Public Videos: {report['youtube_channel'].get('public_videos_count')}")
    print(f"  • Private Review Drafts: {len([v for v in report['youtube_channel'].get('recent_videos', []) if v['privacy'] == 'private'])}")

    print(f"\n[2] Instagram Account: @{report['instagram_account'].get('username')}")
    print(f"  • Followers: {report['instagram_account'].get('followers')}")
    print(f"  • Media Count: {report['instagram_account'].get('media_count')}")

    print(f"\n[3] Content Rights & Safety Gate:")
    print(f"  • Verified Direct Licenses: {report['rights_audit'].get('verified_licenses_count')}")
    print(f"  • Blocked Unlicensed Clips: {report['rights_audit'].get('blocked_clips_count')} (Held in review queue)")
    print(f"  • Approved Clips: {report['rights_audit'].get('approved_clips_count')}")
    print("\n" + "=" * 65 + "\n")

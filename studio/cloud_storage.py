"""
PeakCut Cloud Media & Zero-PC Storage Engine
============================================
Ensures video clips do NOT consume local PC hard drive storage.
1. Automatically uploads finished clips to high-speed Cloud CDN / S3.
2. Provides direct public HTTPS streaming & download links for the user.
3. Automatically purges heavy local raw VODs and local MP4 files after cloud sync.
4. Directly feeds cloud URLs to Meta Instagram API and streams to YouTube Data API.
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

ROOT = Path("C:/peakcut")
sys.path.insert(0, str(ROOT))

CONFIG_FILE = ROOT / "config" / "cloud_config.json"
STAGED_DIR = ROOT / "viral_exports" / "ready_to_post"
SPONZ_DIR = ROOT / "viral_exports" / "sponz_channel_staged"

logger = logging.getLogger("PeakCutCloudStorage")


def load_cloud_config() -> dict:
    """Loads cloud storage configuration."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to read cloud config: {e}")
    return {
        "enabled": True,
        "zero_pc_storage": True,
        "provider": "managed_cdn",
        "auto_upload_on_render": True,
        "purge_local_after_upload": True,
        "purge_raw_vods_immediately": true,
    }


def save_cloud_config(cfg: dict):
    """Saves cloud storage configuration."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def upload_file_to_cloud(filepath: Path) -> Optional[str]:
    """
    Uploads a media file (MP4 or JPG) to high-speed Cloud CDN.
    Returns direct public HTTPS streamable link, or None on error.
    """
    if not filepath.exists() or filepath.stat().st_size == 0:
        logger.warning(f"Cannot upload missing or empty file: {filepath}")
        return None

    import requests

    cfg = load_cloud_config()
    provider = cfg.get("provider", "managed_cdn")

    # Custom S3 Provider
    if provider == "custom_s3" and cfg.get("custom_s3", {}).get("enabled"):
        try:
            import boto3
            from botocore.client import Config
            s3_cfg = cfg["custom_s3"]
            s3 = boto3.client(
                's3',
                endpoint_url=s3_cfg.get("endpoint_url"),
                aws_access_key_id=s3_cfg.get("access_key"),
                aws_secret_access_key=s3_cfg.get("secret_key"),
                config=Config(signature_version='s3v4')
            )
            bucket = s3_cfg["bucket_name"]
            key = f"clips/{filepath.name}"
            content_type = "video/mp4" if filepath.suffix.lower() == ".mp4" else "image/jpeg"
            s3.upload_file(str(filepath), bucket, key, ExtraArgs={"ContentType": content_type})
            base = s3_cfg.get("public_base_url") or f"{s3_cfg.get('endpoint_url')}/{bucket}"
            return f"{base.rstrip('/')}/{key}"
        except Exception as e:
            logger.error(f"S3 upload failed for {filepath.name}: {e}. Falling back to managed CDN.")

    # High-Speed Managed Cloud CDN (Catbox / Litterbox)
    headers = {"User-Agent": "PeakCut-Cloud-Agent/1.0"}
    retries = 3
    for attempt in range(retries):
        try:
            with open(filepath, "rb") as f:
                res = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": (filepath.name, f)},
                    headers=headers,
                    timeout=90
                )
            if res.status_code == 200 and res.text.startswith("http"):
                url = res.text.strip()
                logger.info(f"Cloud CDN Uploaded: {filepath.name} -> {url}")
                return url
            else:
                logger.warning(f"Upload attempt {attempt+1} unexpected response: {res.status_code} - {res.text[:100]}")
        except Exception as ex:
            logger.warning(f"Upload attempt {attempt+1} exception for {filepath.name}: {ex}")
            time.sleep(2)

    return None


def sync_clip_to_cloud(meta: dict, purge_local: bool = True) -> dict:
    """
    Syncs a staged clip's video and cover art to the cloud.
    Stores direct stream & download links in meta.
    If purge_local is True, deletes the heavy local MP4 to preserve PC disk space.
    """
    cid = meta.get("id")
    video_path_str = meta.get("video_path")
    cover_path_str = meta.get("cover_path")

    # Already cloud hosted?
    if meta.get("is_cloud_hosted") and meta.get("cloud_url"):
        return meta

    video_path = Path(video_path_str) if video_path_str else None
    cover_path = Path(cover_path_str) if cover_path_str else None

    # 1. Upload Video
    cloud_video_url = None
    if video_path and video_path.exists() and not str(video_path).startswith("http"):
        v_size_mb = video_path.stat().st_size / (1024 * 1024)
        logger.info(f"Offloading clip [{cid}] ({v_size_mb:.2f} MB) to Cloud CDN...")
        cloud_video_url = upload_file_to_cloud(video_path)
    elif str(video_path).startswith("http"):
        cloud_video_url = str(video_path)

    # 2. Upload Cover Image (Optional)
    cloud_cover_url = None
    if cover_path and cover_path.exists() and not str(cover_path).startswith("http"):
        cloud_cover_url = upload_file_to_cloud(cover_path)
    elif str(cover_path).startswith("http"):
        cloud_cover_url = str(cover_path)

    if cloud_video_url:
        meta["cloud_url"] = cloud_video_url
        meta["cloud_download_url"] = cloud_video_url
        if cloud_cover_url:
            meta["cloud_cover_url"] = cloud_cover_url
        meta["is_cloud_hosted"] = True
        meta["cloud_provider"] = "managed_cdn"
        meta["cloud_uploaded_at"] = time.time()

        # 3. Purge Heavy Local File to ensure zero PC disk clutter
        if purge_local and video_path and video_path.exists():
            try:
                freed_bytes = video_path.stat().st_size
                video_path.unlink(missing_ok=True)
                meta["local_purged"] = True
                meta["video_path"] = cloud_video_url
                meta["disk_freed_mb"] = round(freed_bytes / (1024 * 1024), 2)
                logger.info(f"Zero-PC Storage: Purged local file {video_path.name}. Reclaimed {meta['disk_freed_mb']} MB on PC disk.")
            except Exception as e_del:
                logger.warning(f"Could not purge local video file: {e_del}")

        # Update metadata file on disk
        for target_dir in (STAGED_DIR, SPONZ_DIR):
            mf = target_dir / f"{cid}_meta.json"
            if mf.exists():
                try:
                    mf.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                except Exception:
                    pass

    return meta


def sync_all_staged_clips(purge_local: bool = True) -> dict:
    """
    Iterates all staged clips across ready_to_post and sponz_channel_staged.
    Uploads any unsynced clips to the cloud and purges local video files.
    Returns summary statistics.
    """
    total_found = 0
    synced_count = 0
    total_freed_bytes = 0

    all_meta_files = list(STAGED_DIR.glob("*_meta.json")) + list(SPONZ_DIR.glob("*_meta.json"))

    for mf in all_meta_files:
        try:
            meta = json.loads(mf.read_text(encoding="utf-8"))
            cid = meta.get("id")
            total_found += 1

            if meta.get("is_cloud_hosted") and meta.get("cloud_url"):
                continue

            vpath = Path(meta.get("video_path", ""))
            if vpath.exists():
                v_size = vpath.stat().st_size
                updated_meta = sync_clip_to_cloud(meta, purge_local=purge_local)
                if updated_meta.get("is_cloud_hosted"):
                    synced_count += 1
                    total_freed_bytes += v_size
        except Exception as e:
            logger.warning(f"Error processing meta file {mf.name}: {e}")

    freed_mb = round(total_freed_bytes / (1024 * 1024), 2)
    freed_gb = round(freed_mb / 1024, 2)
    logger.info(f"Cloud Sync Complete: Synced {synced_count}/{total_found} clips. Reclaimed {freed_mb} MB ({freed_gb} GB) on PC disk.")
    return {
        "ok": True,
        "total_clips": total_found,
        "newly_synced": synced_count,
        "reclaimed_mb": freed_mb,
        "reclaimed_gb": freed_gb
    }


def purge_raw_job_media(job_dir: Path) -> float:
    """
    Safely purges multi-gigabyte raw source videos and audio files from a completed job directory.
    Strictly preserves job.json, words.json, and thumbnail.
    Returns reclaimed MB.
    """
    if not job_dir.exists():
        return 0.0

    freed_bytes = 0
    raw_stems = ("source", "audio_src", "source.wav", "audio", "input")
    raw_extensions = (".part", ".ytdl", ".tmp")

    try:
        for f in os.listdir(job_dir):
            fp = job_dir / f
            if fp.is_file():
                if any(fp.name.startswith(s) for s in raw_stems) or any(fp.name.endswith(ext) for ext in raw_extensions):
                    try:
                        sz = fp.stat().st_size
                        fp.unlink(missing_ok=True)
                        freed_bytes += sz
                    except Exception:
                        pass
        # Also clean raw .src.mp4 in clips/ folder
        clips_dir = job_dir / "clips"
        if clips_dir.exists():
            for cf in os.listdir(clips_dir):
                cfp = clips_dir / cf
                if cfp.is_file() and (cfp.name.endswith(".src.mp4") or cfp.name.endswith(".part")):
                    try:
                        sz = cfp.stat().st_size
                        cfp.unlink(missing_ok=True)
                        freed_bytes += sz
                    except Exception:
                        pass
    except Exception as e:
        logger.warning(f"Error purging raw media in {job_dir}: {e}")

    return round(freed_bytes / (1024 * 1024), 2)


def purge_all_raw_vods() -> float:
    """
    Scans entire data/ directory and wipes raw multi-gigabyte source streams from all past jobs.
    Reclaims gigabytes of disk space instantly.
    """
    total_freed_bytes = 0
    search_dirs = [
        ROOT / "data" / "users" / "u_local" / "jobs",
        ROOT / "data" / "users" / "u_local" / "creators"
    ]

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for root, dirs, files in os.walk(s_dir):
            for f in files:
                fp = Path(root) / f
                # Target multi-GB uncut streams & temporary chunks
                is_raw_vod = f in ("source.mp4", "audio_src.m4a", "source.wav", "audio.m4a") or f.endswith(".src.mp4") or f.endswith(".part")
                if is_raw_vod:
                    try:
                        sz = fp.stat().st_size
                        fp.unlink(missing_ok=True)
                        total_freed_bytes += sz
                    except Exception:
                        pass

    freed_mb = round(total_freed_bytes / (1024 * 1024), 2)
    logger.info(f"Purged all raw VOD streams across system. Reclaimed {freed_mb} MB ({freed_mb/1024:.2f} GB) on PC disk.")
    return freed_mb


def get_ephemeral_video_path(meta: dict) -> Tuple[Optional[Path], bool]:
    """
    Retrieves a streamable local path for a clip.
    If local file exists, returns (path, False).
    If local file was purged and clip is in the cloud, streams into an ephemeral temp file.
    Caller MUST call temp_path.unlink() if is_temp is True when done.
    """
    vpath = meta.get("video_path")
    if vpath and Path(vpath).exists() and not str(vpath).startswith("http"):
        return Path(vpath), False

    cloud_url = meta.get("cloud_url") or (vpath if str(vpath).startswith("http") else None)
    if not cloud_url:
        return None, False

    import requests
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        logger.info(f"Streaming ephemeral bytes from cloud ({cloud_url}) for platform publishing...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with requests.get(cloud_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(temp_path, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f_out.write(chunk)

        return temp_path, True
    except Exception as e:
        logger.error(f"Failed to stream ephemeral video from cloud URL {cloud_url}: {e}")
        return None, False


def get_cloud_status() -> dict:
    """Returns overview of cloud storage and PC disk savings."""
    all_meta_files = list(STAGED_DIR.glob("*_meta.json")) + list(SPONZ_DIR.glob("*_meta.json"))
    total_clips = len(all_meta_files)
    cloud_clips = 0
    total_saved_mb = 0.0

    for mf in all_meta_files:
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            if m.get("is_cloud_hosted") or m.get("cloud_url"):
                cloud_clips += 1
                total_saved_mb += m.get("disk_freed_mb", 35.0)
        except Exception:
            pass

    cfg = load_cloud_config()
    return {
        "enabled": cfg.get("enabled", True),
        "zero_pc_storage": cfg.get("zero_pc_storage", True),
        "provider": cfg.get("provider", "managed_cdn"),
        "total_clips": total_clips,
        "cloud_hosted_clips": cloud_clips,
        "disk_saved_mb": round(total_saved_mb, 2),
        "disk_saved_gb": round(total_saved_mb / 1024, 2)
    }

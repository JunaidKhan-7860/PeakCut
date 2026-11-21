"""
PeakCut Content Rights & Licensing Verification
==============================================
Enforces strict licensing and permission compliance before publishing content.
Rule: Edits and captions alone do not prove rights. Clips must have documented
permission or a valid license before being eligible for public broadcast.
"""
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any

ROOT = Path("C:/peakcut")
CONFIG_DIR = ROOT / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LICENSES_FILE = CONFIG_DIR / "licenses.json"

logger = logging.getLogger("PeakCutRights")


def load_licenses() -> dict:
    if LICENSES_FILE.exists():
        try:
            return json.loads(LICENSES_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Error reading licenses file: {e}")
    # Default template
    return {
        "verified_creators": {},
        "campaign_agreements": {
            # Active clipping campaign agreements documented by user
            # e.g., "AsianJeff": {"campaign_id": "AsianJeff_Nov19", "terms": "Non-negative, No logos, #AsianJeff", "verified": False}
        },
        "default_policy": "review_required"
    }


def save_licenses(data: dict):
    LICENSES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check_rights(creator_id: str, campaign_name: str = "") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verifies if a creator's stream content has documented permission or a confirmed license.
    Returns:
        (is_authorized, reason, license_metadata)
    """
    licenses = load_licenses()
    verified_creators = licenses.get("verified_creators", {})
    campaigns = licenses.get("campaign_agreements", {})
    
    # 1. Direct creator license / signed permission
    if creator_id in verified_creators:
        entry = verified_creators[creator_id]
        if entry.get("status") == "approved":
            return True, f"Verified direct license on file: {entry.get('license_id', 'Direct')}", entry
            
    # 2. Campaign bounty authorization
    # If the creator is part of an official sponsored campaign (e.g., ReachClipping / RUCKUS),
    # verify that the campaign terms and license documentation have been explicitly confirmed.
    for c_key, c_info in campaigns.items():
        if (c_key.lower() in creator_id.lower() or c_key.lower() in campaign_name.lower()) and c_info.get("verified"):
            return True, f"Verified campaign bounty authorization: {c_info.get('campaign_id')}", c_info
            
    # 3. Not verified - enforce hard policy
    reason = (
        f"Source creator '{creator_id}' does not have a verified license or documented written permission on file. "
        "Edits and captions alone do not confer rights. Clip routed to local review queue."
    )
    return False, reason, {}


def register_campaign_license(creator_or_campaign: str, license_info: dict):
    """Registers documented written permission or verified campaign terms for a creator."""
    licenses = load_licenses()
    licenses.setdefault("campaign_agreements", {})[creator_or_campaign] = license_info
    save_licenses(licenses)
    logger.info(f"Registered campaign license for: {creator_or_campaign}")

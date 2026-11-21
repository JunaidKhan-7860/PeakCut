"""
PeakCut Safe Platform Poster
============================
Delegates background uploads to official studio.uploader module.
Enforces content rights and defaults to private/unlisted review queue.
"""
import logging
import sys
from pathlib import Path

ROOT = Path("C:/peakcut")
sys.path.insert(0, str(ROOT))

from studio import uploader

logger = logging.getLogger("AutoPoster")


def post_next_due() -> bool:
    """Invokes official uploader to process review queue under strict rights verification."""
    try:
        uploader.process_review_queue()
        return True
    except Exception as e:
        logger.error(f"Error processing review queue: {e}")
        return False


if __name__ == "__main__":
    uploader.print_status()
    uploader.process_review_queue()

"""
Universal In-Memory OSINT Cache Manager
Provides centralized inspection, invalidation, and developer override controls for all sub-prober caches.
"""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger("cache_manager")

def is_cache_disabled() -> bool:
    """Returns True if the developer explicitly disabled in-memory caching via environment variable."""
    return os.environ.get("OSINT_DISABLE_CACHE", "").strip() in ("1", "true", "True", "TRUE")

def clear_all_caches():
    """Wipes every in-memory cache clean across all OSINT prober subsystems."""
    try:
        from backend import live_osint
        getattr(live_osint, "_DEEP_OSINT_CACHE", {}).clear()
        getattr(live_osint, "_GIT_ARCHAEOLOGY_CACHE", {}).clear()
        getattr(live_osint, "_OPENPGP_CACHE", {}).clear()
        getattr(live_osint, "_GRAVATAR_CACHE", {}).clear()
    except Exception as e:
        logger.debug(f"Cache clear error in live_osint: {e}")

    try:
        from backend import image_recon
        getattr(image_recon, "_IMAGE_HARVEST_CACHE", {}).clear()
        getattr(image_recon, "_AVATAR_PROBE_CACHE", {}).clear()
    except Exception as e:
        logger.debug(f"Cache clear error in image_recon: {e}")

    try:
        from backend import browser_runner
        getattr(browser_runner, "_LINKEDIN_BROWSER_CACHE", {}).clear()
    except Exception as e:
        logger.debug(f"Cache clear error in browser_runner: {e}")

    try:
        from backend import facebook_recon
        getattr(facebook_recon, "_FB_SCRAPE_CACHE", {}).clear()
    except Exception as e:
        logger.debug(f"Cache clear error in facebook_recon: {e}")

    try:
        from backend import osint_scanner
        getattr(osint_scanner, "_BREACH_CACHE", {}).clear()
    except Exception as e:
        logger.debug(f"Cache clear error in osint_scanner: {e}")

    try:
        from backend import wmn_engine
        getattr(wmn_engine, "_WMN_RESULT_CACHE", {}).clear()
    except Exception as e:
        logger.debug(f"Cache clear error in wmn_engine: {e}")

    try:
        from backend import web_dork_recon
        getattr(web_dork_recon, "_DORK_CACHE", {}).clear()
        getattr(web_dork_recon, "_SNIPPET_CACHE", {}).clear()
    except Exception as e:
        logger.debug(f"Cache clear error in web_dork_recon: {e}")

def invalidate_target_caches(email: Optional[str] = None, target_name: Optional[str] = None):
    """
    Selectively purges cached probe results for a specific target identity.
    Called when refresh=True is requested to guarantee a 100% fresh, live re-scan.
    """
    clean_e = (email or "").strip().lower()
    clean_n = (target_name or "").strip().lower()

    if not clean_e and not clean_n:
        clear_all_caches()
        return

    def _purge_dict(d, needle: str):
        if not d or not isinstance(d, dict) or not needle:
            return
        keys_to_del = [k for k in d.keys() if needle in str(k).lower()]
        for k in keys_to_del:
            d.pop(k, None)

    try:
        from backend import live_osint
        _purge_dict(getattr(live_osint, "_DEEP_OSINT_CACHE", None), clean_e)
        _purge_dict(getattr(live_osint, "_GIT_ARCHAEOLOGY_CACHE", None), clean_e)
        _purge_dict(getattr(live_osint, "_OPENPGP_CACHE", None), clean_e)
        _purge_dict(getattr(live_osint, "_GRAVATAR_CACHE", None), clean_e)
        if clean_n:
            _purge_dict(getattr(live_osint, "_DEEP_OSINT_CACHE", None), clean_n)
    except Exception as e:
        logger.debug(f"Selective cache purge error in live_osint: {e}")

    try:
        from backend import image_recon
        _purge_dict(getattr(image_recon, "_IMAGE_HARVEST_CACHE", None), clean_e)
        _purge_dict(getattr(image_recon, "_AVATAR_PROBE_CACHE", None), clean_e)
    except Exception as e:
        logger.debug(f"Selective cache purge error in image_recon: {e}")

    try:
        from backend import browser_runner
        _purge_dict(getattr(browser_runner, "_LINKEDIN_BROWSER_CACHE", None), clean_e)
        if clean_n:
            _purge_dict(getattr(browser_runner, "_LINKEDIN_BROWSER_CACHE", None), clean_n)
    except Exception as e:
        logger.debug(f"Selective cache purge error in browser_runner: {e}")

    try:
        from backend import facebook_recon
        _purge_dict(getattr(facebook_recon, "_FB_SCRAPE_CACHE", None), clean_e)
        if clean_n:
            _purge_dict(getattr(facebook_recon, "_FB_SCRAPE_CACHE", None), clean_n)
    except Exception as e:
        logger.debug(f"Selective cache purge error in facebook_recon: {e}")

    try:
        from backend import osint_scanner
        _purge_dict(getattr(osint_scanner, "_BREACH_CACHE", None), clean_e)
    except Exception as e:
        logger.debug(f"Selective cache purge error in osint_scanner: {e}")

    try:
        from backend import web_dork_recon
        _purge_dict(getattr(web_dork_recon, "_DORK_CACHE", None), clean_e)
        _purge_dict(getattr(web_dork_recon, "_SNIPPET_CACHE", None), clean_e)
        if clean_n:
            _purge_dict(getattr(web_dork_recon, "_DORK_CACHE", None), clean_n)
            _purge_dict(getattr(web_dork_recon, "_SNIPPET_CACHE", None), clean_n)
    except Exception as e:
        logger.debug(f"Selective cache purge error in web_dork_recon: {e}")

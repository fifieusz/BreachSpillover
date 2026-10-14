"""
BreachSpillover - Identity Arbiter Verdict Store

Persists the AI Cardinal arbiter verdict produced during a scan so that the
entity resolution engine can consume it when a dossier is (re)loaded, without
touching the SQLite schema. Verdicts are stored as JSON sidecar files under
`data/arbiter_verdicts/`, keyed by a SHA-256 digest of the normalised seed.
"""

import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("breach_spillover.arbiter_store")

BASE_DIR = Path(__file__).resolve().parent.parent
STORE_DIR = BASE_DIR / "data" / "arbiter_verdicts"

# Only the fields the clustering engine needs are persisted.
_PERSISTED_KEYS = (
    "real_name", "perceived_gender", "pronouns", "aliases", "alias_personas",
    "verified_profiles", "namesake_collisions", "speculative_probes",
    "rejected_profiles", "arbiter_mode",
)


def _key(seed: str) -> str:
    return hashlib.sha256((seed or "").strip().lower().encode("utf-8")).hexdigest()


def _path(seed: str, store_dir: Optional[Path] = None) -> Path:
    return (store_dir or STORE_DIR) / f"{_key(seed)}.json"


def save_verdict(seed: str, verdict: Dict[str, Any], store_dir: Optional[Path] = None) -> bool:
    """Atomically writes the verdict. Returns False (never raises) on failure."""
    if not seed or not isinstance(verdict, dict):
        return False
    try:
        target = _path(seed, store_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: verdict.get(k) for k in _PERSISTED_KEYS if k in verdict}
        payload["_saved_at"] = time.time()
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, default=str)
        os.replace(tmp, target)
        return True
    except Exception as e:
        logger.warning(f"Could not persist arbiter verdict: {e}")
        return False


def load_verdict(seed: str, store_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Returns the stored verdict, or an empty dict when absent/corrupt."""
    if not seed:
        return {}
    try:
        p = _path(seed, store_dir)
        if not p.exists():
            return {}
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.debug(f"Could not load arbiter verdict: {e}")
        return {}

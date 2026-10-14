"""
BreachSpillover - Autonomous Cardinal Intelligence System
Unified cognitive architecture consolidating:
  - Cardinal Core: Autonomous thinking, reflection, and multi-hop pivot loop.
  - Cardinal Arbiter: Identity disambiguation, zero-contradiction gatekeeper, and candidate quarantine.
  - Cardinal LLM: Zero-dependency inference engine (Groq / Gemini) and threat dossier synthesis.
"""

from backend.cardinal.core import (
    CardinalIntelligenceCore,
    CardinalThought,
    CardinalInvestigationResult,
)
from backend.cardinal.arbiter import (
    synthesize_identity_from_observations,
    build_observation_manifest,
    ai_verify_and_quarantine_candidates,
    _enforce_cardinal_strictness,
    clean_text_symbols,
    normalize_string,
)
from backend.cardinal.llm import (
    call_groq_api,
    call_gemini_api,
    resolve_api_key,
    test_ai_connection,
    load_dotenv,
    generate_ai_threat_dossier,
    generate_heuristic_fallback_dossier,
    build_target_forensic_context,
    ai_copilot_chat,
    GROQ_DEFAULT_MODEL,
    GEMINI_DEFAULT_MODEL,
)

# Cardinal is the unified master interface
Cardinal = CardinalIntelligenceCore

__all__ = [
    "Cardinal",
    "CardinalIntelligenceCore",
    "CardinalThought",
    "CardinalInvestigationResult",
    "synthesize_identity_from_observations",
    "build_observation_manifest",
    "ai_verify_and_quarantine_candidates",
    "_enforce_cardinal_strictness",
    "clean_text_symbols",
    "normalize_string",
    "call_groq_api",
    "call_gemini_api",
    "resolve_api_key",
    "test_ai_connection",
    "load_dotenv",
    "generate_ai_threat_dossier",
    "generate_heuristic_fallback_dossier",
    "build_target_forensic_context",
    "ai_copilot_chat",
    "GROQ_DEFAULT_MODEL",
    "GEMINI_DEFAULT_MODEL",
]

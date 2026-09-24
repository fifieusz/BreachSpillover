import sys
sys.path.insert(0, ".")
import json
import traceback
from backend.ai_engine import (
    generate_ai_threat_dossier,
    generate_heuristic_fallback_dossier,
    resolve_api_key,
    call_groq_api,
    SYSTEM_PROMPT_DOSSIER,
    build_target_forensic_context,
    GROQ_DEFAULT_MODEL
)

scan_data = {'employee': {'corporate_email': 'sjoerdsikkema79@gmail.com', 'full_name': 'Sjoerd Sikkema'}}
clean_key = resolve_api_key('groq')
forensic_text = build_target_forensic_context(scan_data)
prompt = (
    "Generate a comprehensive, analytical Threat Dossier for the following scanned target forensic data.\n\n"
    f"{forensic_text}\n\n"
    "Return ONLY the requested JSON object matching the schema."
)

try:
    res = call_groq_api(prompt=prompt, system_instruction=SYSTEM_PROMPT_DOSSIER, api_key=clean_key, response_json=True, max_tokens=650)
    print("res success:", res.get("success"), "error:", res.get("error"))
    raw_text = res["text"].strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    parsed = json.loads(raw_text.strip())
    print("Parsed JSON keys:", list(parsed.keys()))
    print("AI generation test succeeded!")
except Exception as e:
    traceback.print_exc()

dossier = generate_ai_threat_dossier(scan_data, force_refresh=True)
print("dossier is_ai_generated:", dossier.get("is_ai_generated"))
print("dossier provider:", dossier.get("provider"))
print("dossier model:", dossier.get("model"))
print("dossier notice:", dossier.get("notice"))

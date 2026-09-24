import sys
sys.path.insert(0, ".")
from backend.main import search_exposure
from backend.ai_engine import resolve_api_key, call_groq_api, SYSTEM_PROMPT_DOSSIER

scan_data = search_exposure('jordinzwaan2016@gmail.com', audit_mode=True)
clean_key = resolve_api_key('groq', '')

emp = scan_data.get('employee', {})
pivots = scan_data.get('pivots', [])
top_pivots = [p for p in pivots if p.get('confidence_score', 0) >= 0.8][:12]
p_lines = '\n'.join([f"- [{p.get('pivot_type')}] {p.get('pivot_value')} (Confidence: {p.get('confidence_score')})" for p in top_pivots])

foots = scan_data.get('physical_footprints', [])
city = foots[0].get('city', 'Unknown') if foots else 'Unknown'

concise_context = (
    f"TARGET EMAIL: {emp.get('corporate_email')}\n"
    f"RESOLVED NAME: {emp.get('full_name')}\n"
    f"ROLE / ORG: {emp.get('job_title')} ({emp.get('department')})\n"
    f"LOCATION: {city}\n"
    f"TOP CORROBORATED PIVOTS:\n{p_lines}"
)
print("Concise context length:", len(concise_context))

prompt = (
    "Generate a comprehensive, analytical Threat Dossier for the following scanned target forensic data.\n\n"
    f"{concise_context}\n\n"
    "Return strictly a valid JSON object conforming to the schema."
)

for m in ['openai/gpt-oss-20b', 'qwen/qwen3.8-27b']:
    res = call_groq_api(prompt=prompt, system_instruction=SYSTEM_PROMPT_DOSSIER, api_key=clean_key, model=m, response_json=True, max_tokens=650)
    print(m, "success:", res.get("success"), "latency:", res.get("latency_seconds"), "error:", res.get("error"))

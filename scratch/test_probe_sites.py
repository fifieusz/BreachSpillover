import urllib.request
import re
from typing import Dict, Any, List

USER_AGENT_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def probe_personal_sites(target_name: str, target_email: str, known_handles: List[str]):
    local_part = target_email.split("@")[0].lower() if "@" in target_email else ""
    candidate_handles = []
    if local_part:
        candidate_handles.append(local_part)
        base_h = re.sub(r'\d+$', '', local_part)
        if base_h and base_h != local_part and len(base_h) >= 4:
            candidate_handles.append(base_h)
    clean_name = target_name.lower().replace(" ", "").replace(".", "")
    if clean_name and clean_name not in candidate_handles:
        candidate_handles.append(clean_name)
    for h in known_handles:
        if h not in candidate_handles:
            candidate_handles.append(h)

    print("Candidate handles to probe:", candidate_handles)
    probe_templates = [
        "https://{h}.wixsite.com/portfolio",
        "https://{h}.wixsite.com/{h}",
        "https://{h}.jouwweb.nl",
        "https://{h}.github.io",
        "https://{h}.wordpress.com",
        "https://{h}.carrd.co",
    ]

    discovered = []
    for h in candidate_handles:
        for tmpl in probe_templates:
            url = tmpl.format(h=h)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT_DESKTOP})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status == 200:
                        print("  [DISCOVERED SITE] -->", url)
                        discovered.append(url)
            except Exception:
                pass
    return discovered

sites = probe_personal_sites("Jordin Zwaan", "jordinzwaan2016@gmail.com", ["jordinzwaan", "sazeku"])
print("Discovered sites:", sites)

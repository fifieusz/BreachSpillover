import sys
sys.path.insert(0, '.')
from backend.web_dork_recon import query_duckduckgo_lite

print("Testing DDG lite:")
snips = query_duckduckgo_lite("Yasir Kadhim", 10)
print("DDG lite count:", len(snips))
for s in snips:
    print("DDG:", s["title"], "->", s["url"], "|", s["snippet"][:80])

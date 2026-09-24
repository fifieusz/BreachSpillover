import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.web_dork_recon import query_duckduckgo_lite, query_bing_search, query_yahoo_search

q = "Sjoerd Sikkema"
print("Testing DuckDuckGo Lite:")
try:
    ddg = query_duckduckgo_lite(q, max_results=5)
    print("  DDG Lite count:", len(ddg))
    for s in ddg[:2]: print("   ", s)
except Exception as e:
    print("  DDG Lite error:", e)

print("\nTesting Bing Search:")
try:
    b = query_bing_search(q, max_results=5)
    print("  Bing count:", len(b))
    for s in b[:2]: print("   ", s)
except Exception as e:
    print("  Bing error:", e)

print("\nTesting Yahoo Search:")
try:
    y = query_yahoo_search(q, max_results=5)
    print("  Yahoo count:", len(y))
    for s in y[:2]: print("   ", s)
except Exception as e:
    print("  Yahoo error:", e)

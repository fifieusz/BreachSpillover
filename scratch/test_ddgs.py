from duckduckgo_search import DDGS

query = '"Sjoerd Sikkema"'
print(f"Testing DDGS text search for: {query}")
try:
    results = list(DDGS().text(query, max_results=8))
    print(f"DDGS returned {len(results)} results:")
    for r in results:
        title = str(r.get("title", "")).encode("ascii", "replace").decode("ascii")
        href = str(r.get("href", ""))
        body = str(r.get("body", "")).encode("ascii", "replace").decode("ascii")
        print(f"  [{title[:60]}]\n   -> {href}\n   Snippet: {body[:100]}\n")
except Exception as e:
    print("DDGS Error:", e)

# Also test without quotes
query2 = 'Sjoerd Sikkema Wolvega'
print(f"\nTesting DDGS text search for: {query2}")
try:
    results2 = list(DDGS().text(query2, max_results=8))
    print(f"DDGS returned {len(results2)} results:")
    for r in results2:
        title = str(r.get("title", "")).encode("ascii", "replace").decode("ascii")
        href = str(r.get("href", ""))
        body = str(r.get("body", "")).encode("ascii", "replace").decode("ascii")
        print(f"  [{title[:60]}]\n   -> {href}\n   Snippet: {body[:100]}\n")
except Exception as e:
    print("DDGS Error:", e)

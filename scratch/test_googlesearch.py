from googlesearch import search

query = 'Sjoerd Sikkema'
print(f"Testing Google Search for: {query}")
try:
    results = list(search(query, num_results=6, advanced=True))
    print(f"Google returned {len(results)} results:")
    for r in results:
        title = str(r.title).encode("ascii", "replace").decode("ascii")
        url = str(r.url)
        desc = str(r.description).encode("ascii", "replace").decode("ascii")
        print(f"  Title: {title}\n  URL: {url}\n  Description: {desc[:100]}\n")
except Exception as e:
    print("Google search error:", e)

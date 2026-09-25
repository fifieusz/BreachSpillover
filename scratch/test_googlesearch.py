from googlesearch import search
import sys
sys.stdout.reconfigure(encoding='utf-8')

for q in ['"Alje Woltjer"', 'site:linkedin.com/in "Alje Woltjer"', 'Alje Woltjer Vooruit']:
    try:
        results = list(search(q, num_results=5, advanced=True))
        print(f"=== Query: {q} | Results: {len(results)} ===")
        for r in results:
            print("  Title:", r.title)
            print("  URL:", r.url)
            print("  Desc:", r.description[:100])
    except Exception as e:
        print(f"Google error for {q}: {e}")

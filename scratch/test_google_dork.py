from googlesearch import search

def test_google():
    queries = [
        '"3gbxdd@gmail.com"',
        '"3gbxdd"',
        'site:linkedin.com "3gbxdd"',
        'site:pinterest.com/3gbxdd',
    ]
    for q in queries:
        print(f"\n--- Google Query: {q} ---")
        try:
            results = list(search(q, num_results=5))
            print(f"Count: {len(results)}")
            for r in results:
                print("  ->", r)
        except Exception as e:
            print("  Error:", e)

if __name__ == "__main__":
    test_google()

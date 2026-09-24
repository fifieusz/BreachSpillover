import sys
sys.path.insert(0, ".")
from duckduckgo_search import DDGS
from backend.web_dork_recon import _scrape_bing_html_direct, _scrape_yahoo_direct

def test_engines():
    target = "3gbxdd@gmail.com"
    handle = "3gbxdd"
    print("Testing DDG for exact email...")
    try:
        ddgs = DDGS()
        res = list(ddgs.text(f'"{target}"', max_results=5))
        print("DDG email results:", len(res))
        for r in res:
            print("  ", r)
        res_h = list(ddgs.text(f'"{handle}"', max_results=5))
        print("DDG handle results:", len(res_h))
        for r in res_h:
            print("  ", r)
    except Exception as e:
        print("DDG error:", e)

    print("\nTesting Bing direct for email...")
    bing_res = _scrape_bing_html_direct(f'"{target}"', max_results=5)
    print("Bing email results:", len(bing_res))
    for r in bing_res:
        print("  ", r.get("title"), r.get("url"))

    print("\nTesting Bing direct for handle...")
    bing_h = _scrape_bing_html_direct(f'"{handle}"', max_results=5)
    print("Bing handle results:", len(bing_h))
    for r in bing_h:
        print("  ", r.get("title"), r.get("url"))

if __name__ == "__main__":
    test_engines()

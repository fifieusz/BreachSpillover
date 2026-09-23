import urllib.request
import re
import sys

def verify():
    print("Verifying frontend asset delivery from running server...", flush=True)
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf\ufe0f]')
    
    # 1. Verify index.html
    with urllib.request.urlopen("http://127.0.0.1:8000/") as resp:
        html = resp.read().decode("utf-8")
        assert "[OSINT_FEEDS: ACTIVE]" not in html, "Found [OSINT_FEEDS: ACTIVE] in HTML!"
        assert "Zero-Dependency Cloud LLM Inference" not in html, "Found AI modal fluff in HTML!"
        assert "Zero-Weight Cloud Inference" not in html, "Found AI modal disclaimer in HTML!"
        m = emoji_pattern.findall(html)
        assert len(m) == 0, f"Found emojis in HTML: {m}"
        print("[PASS] index.html: 0 emojis, 0 filler marketing text", flush=True)

    # 2. Verify style.css
    with urllib.request.urlopen("http://127.0.0.1:8000/static/css/style.css") as resp:
        css = resp.read().decode("utf-8")
        m = emoji_pattern.findall(css)
        assert len(m) == 0, f"Found emojis in CSS: {m}"
        print("[PASS] style.css: 0 emojis", flush=True)

    # 3. Verify app.js
    with urllib.request.urlopen("http://127.0.0.1:8000/static/js/app.js") as resp:
        js = resp.read().decode("utf-8")
        assert "function getUiIcon" in js, "Missing getUiIcon in app.js!"
        assert "PROBED CANDIDATE HANDLES FOR THIS ACCOUNT" not in js, "Found verbose candidate header!"
        assert "Get a free Groq key in 20s" not in js, "Found salesy AI key text!"
        m = emoji_pattern.findall(js)
        assert len(m) == 0, f"Found emojis in JS: {m}"
        print("[PASS] app.js: 0 emojis, getUiIcon active, clean text verified", flush=True)

    print("\nSUCCESS: All UI components are completely purged of emojis and AI filler text!", flush=True)

if __name__ == "__main__":
    verify()

import sys
sys.path.insert(0, ".")
import urllib.request
import json
import time
from backend.ai_engine import resolve_api_key

def test_models():
    key = resolve_api_key("groq")
    models = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    for m in models:
        data = {
            "model": m,
            "messages": [{"role": "user", "content": "Respond strictly with the word OK."}],
            "max_tokens": 50
        }
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(data).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                text = body["choices"][0]["message"]["content"].strip()
                print(f"Model {m}: SUCCESS ({time.time()-t0:.2f}s) -> {text}")
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8")
            print(f"Model {m}: HTTP {e.code} -> {err[:200]}")
        except Exception as e:
            print(f"Model {m}: Exception -> {e}")

if __name__ == "__main__":
    test_models()

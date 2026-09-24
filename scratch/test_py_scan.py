import os
import subprocess
import json
import time

def test_scan():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    out_file = "scratch/fast_test.json"
    if os.path.exists(out_file):
        os.remove(out_file)

    t0 = time.time()
    cmd = [
        "user-scanner",
        "-e", "3gbxdd@gmail.com",
        "--no-nsfw",
        "-C", "40",
        "-c", "Community,Dev,Entertainment,Gaming,Music,Other,Social,Learning",
        "-f", "json",
        "-o", out_file
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    dur = time.time() - t0
    print(f"Subprocess finished in {dur:.2f}s with returncode {res.returncode}")
    print("STDOUT:", res.stdout.encode("ascii", "replace").decode("ascii")[:300])
    print("STDERR:", res.stderr.encode("ascii", "replace").decode("ascii")[:300])
    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            hits = [d for d in data if d.get("status") == "Registered"]
            print(f"Discovered {len(hits)} registered platforms:")
            for h in hits:
                print(f"  {h.get('site_name')}: {h.get('url')} | extra: {h.get('extra')}")

if __name__ == "__main__":
    test_scan()

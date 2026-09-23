import subprocess
import time
import urllib.request
import json
import asyncio
import sys

# Start edge with remote debugging
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    '--remote-debugging-port=9222',
    'http://127.0.0.1:8000'
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

time.sleep(2)

try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5) as r:
        tabs = json.loads(r.read().decode('utf-8'))
        print("Edge tabs:", len(tabs))
        for t in tabs:
            print("Tab:", t.get("title"), "| URL:", t.get("url"))
            print("WS URL:", t.get("webSocketDebuggerUrl"))
except Exception as e:
    print("CDP Error:", e)
finally:
    proc.terminate()

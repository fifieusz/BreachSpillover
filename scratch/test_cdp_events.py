import subprocess
import time
import urllib.request
import json
import asyncio

try:
    import websockets
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

async def check_console():
    proc = subprocess.Popen([
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        '--headless=new',
        '--remote-debugging-port=9222',
        'http://127.0.0.1:8000'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    await asyncio.sleep(2)

    try:
        req = urllib.request.urlopen("http://127.0.0.1:9222/json")
        tabs = json.loads(req.read().decode('utf-8'))
        target_tab = None
        for t in tabs:
            if "8000" in t.get("url", ""):
                target_tab = t
                break
        
        if not target_tab:
            print("No 8000 tab found!")
            return

        ws_url = target_tab["webSocketDebuggerUrl"]
        print("Connecting to:", ws_url)
        async with websockets.connect(ws_url) as ws:
            # Enable Runtime and Log
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Log.enable"}))
            await ws.send(json.dumps({"id": 3, "method": "Page.enable"}))

            # Test clicking a tab button or search button via Runtime.evaluate
            eval_cmd = {
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
                        (function() {
                            let results = [];
                            let btn = document.querySelector('.tab-btn');
                            results.push('Tab btn found: ' + Boolean(btn));
                            if (btn) {
                                btn.click();
                                results.push('Clicked tab btn');
                            }
                            let searchInput = document.getElementById('search-input');
                            results.push('Search input found: ' + Boolean(searchInput));
                            let searchBtn = document.getElementById('search-submit-btn');
                            results.push('Search btn found: ' + Boolean(searchBtn));
                            return results.join(', ');
                        })()
                    """,
                    "returnByValue": True
                }
            }
            await ws.send(json.dumps(eval_cmd))

            start = time.time()
            while time.time() - start < 4:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if data.get("method") == "Runtime.exceptionThrown":
                        print("EXCEPTION THROWN:", data["params"]["exceptionDetails"])
                    elif data.get("method") == "Runtime.consoleAPICalled":
                        print("CONSOLE LOG:", data["params"]["type"], [arg.get("value") for arg in data["params"].get("args", [])])
                    elif data.get("id") == 4:
                        print("EVAL RESULT:", data.get("result", {}).get("result", {}).get("value"))
                except asyncio.TimeoutError:
                    pass
    finally:
        proc.terminate()

asyncio.run(check_console())

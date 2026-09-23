import subprocess
import time
import urllib.request
import json
import asyncio
import websockets

async def check_full_interaction():
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
        
        ws_url = target_tab["webSocketDebuggerUrl"]
        print("Connected to page:", ws_url)
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Log.enable"}))

            # Simulate user typing and searching by clicking btn-search
            test_script = """
                (function() {
                    const input = document.getElementById('search-input');
                    input.value = 'jordinzwaan2016@gmail.com';
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    
                    const btn = document.getElementById('btn-search');
                    btn.click();
                    
                    return 'Clicked btn-search for: ' + input.value;
                })()
            """
            await ws.send(json.dumps({
                "id": 10,
                "method": "Runtime.evaluate",
                "params": {"expression": test_script, "returnByValue": True}
            }))

            # Listen and print console logs as scan progresses
            start = time.time()
            while time.time() - start < 10:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if data.get("method") == "Runtime.exceptionThrown":
                        print("EXCEPTION:", data["params"]["exceptionDetails"])
                    elif data.get("method") == "Runtime.consoleAPICalled":
                        log_type = data["params"]["type"]
                        args = [arg.get("value") for arg in data["params"].get("args", [])]
                        print(f"CONSOLE [{log_type}]:", args)
                    elif data.get("id") == 10:
                        print("SEARCH INITIATED:", data.get("result", {}).get("result", {}).get("value"))
                except asyncio.TimeoutError:
                    pass

            # Inspect DOM results
            verify_script = """
                (function() {
                    const city = document.getElementById('summary-city')?.innerText;
                    const addr = document.getElementById('summary-address')?.innerText;
                    const work = document.getElementById('summary-workplace')?.innerText;
                    const workRole = document.getElementById('summary-workplace-role')?.innerText;
                    const badgeAddr = document.getElementById('badge-lock-address')?.innerText;
                    const targetCard = document.getElementById('target-exposure-card')?.style.display;
                    return JSON.stringify({ city, addr, work, workRole, badgeAddr, targetCard });
                })()
            """
            await ws.send(json.dumps({
                "id": 20,
                "method": "Runtime.evaluate",
                "params": {"expression": verify_script, "returnByValue": True}
            }))

            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(msg)
                    if data.get("id") == 20:
                        print("\nDOM VERIFICATION RESULT:")
                        print(data.get("result", {}).get("result", {}).get("value"))
                        break
                except asyncio.TimeoutError:
                    break
    finally:
        proc.terminate()

asyncio.run(check_full_interaction())

with open('frontend/static/js/app.v17.js', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f, 1):
        if 'networkInstance.on' in line or 'on("click"' in line:
            print(f"{i}: {line.strip()[:100]}")

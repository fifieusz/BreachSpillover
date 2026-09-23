with open('frontend/static/js/app.v17.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if any(k in line.lower() for k in ['color: #fff', 'color:#fff', 'color: white', 'background: #fff', 'background-color: #0e1117', 'background: #0f172a']):
        print(f"Line {idx+1}: {line.strip()[:100]}")

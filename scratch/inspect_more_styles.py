with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

import re

for selector in ['code-field', 'terminal', 'table', 'badge', 'modal', 'drawer', 'btn-primary']:
    matches = re.findall(rf'(\.{selector}[^{{]*\{{[^}}]+\}})', css)
    print(f"=== {selector} ===")
    for m in matches[:2]:
        print(m[:200])
        print()

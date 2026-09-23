with open('frontend/static/css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

import re
shadows = re.findall(r'box-shadow:[^;]+;', css)
print("Unique shadows:")
for s in set(shadows):
    print("  ", s)

with open('frontend/static/js/app.v17.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'(style=[\"\'][^\"\']*(?:background|color|border)[^\"\']*[\"\'])', text)
print(f"Total inline styles with colors in app.v17.js: {len(matches)}")
from collections import Counter
c = Counter(matches)
for m, cnt in c.most_common(20):
    print(f"{cnt:3d}: {m[:100]}")

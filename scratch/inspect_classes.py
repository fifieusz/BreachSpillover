import re
from collections import Counter

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'class="([^"]+)"', text)
all_tokens = [tok for c in matches for tok in c.split()]
color_tokens = [t for t in all_tokens if any(k in t for k in ['bg-', 'text-', 'border-', 'dark:'])]
c = Counter(color_tokens)
print("Top color/dark tokens in index.html:")
for tok, cnt in c.most_common(50):
    print(f'{cnt:3d}: {tok}')

# Check inline styles with color
inline_styles = re.findall(r'style="([^"]+)"', text)
print("\nInline styles with colors/backgrounds:")
for s in inline_styles:
    if any(k in s for k in ['color', 'background', '#', 'rgb']):
        print('  ', s[:100])

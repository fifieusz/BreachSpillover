import re

with open('frontend/static/js/app.v17.js', 'r', encoding='utf-8') as f:
    js = f.read()
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

vars_in_js = set(re.findall(r'var\((--[a-zA-Z0-9_-]+)\)', js))
vars_in_html = set(re.findall(r'var\((--[a-zA-Z0-9_-]+)\)', html))

print("CSS vars in app.v17.js:")
for v in sorted(vars_in_js):
    print("  ", v)

print("\nCSS vars in index.html:")
for v in sorted(vars_in_html):
    print("  ", v)

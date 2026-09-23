import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all IDs containing modal or inspector or drawer or popup
all_ids = re.findall(r'id=["\']([^"\']+)["\']', html)
modal_ids = [i for i in all_ids if any(k in i.lower() for k in ['modal', 'drawer', 'inspector', 'dialog', 'popup'])]
print("Interactive IDs:", modal_ids)

# Check all classes on sections and cards
sections = re.findall(r'<(?:section|div|aside|header|nav)[^>]*class=["\']([^"\']+)["\']', html)
print("\nUnique section/container classes:")
container_classes = set()
for s in sections:
    for c in s.split():
        if any(k in c for k in ['card', 'panel', 'container', 'modal', 'drawer', 'cockpit', 'table', 'tab', 'header', 'bar']):
            container_classes.add(c)
for c in sorted(container_classes):
    print("  ", c)

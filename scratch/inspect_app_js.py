with open('frontend/static/js/app.v17.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Check occurrences of tile layers or maps
tiles = [line for line in text.splitlines() if any(k in line for k in ['tileLayer', 'L.map', 'carto', 'openstreetmap'])]
print("Tile layers / Map lines:")
for t in tiles:
    print('  ', t.strip()[:100])

# Check vis network groups or options
print("\nVis.Network lines:")
for idx, line in enumerate(text.splitlines()):
    if any(k in line for k in ['vis.Network', 'network = new', 'const options =', 'groups: {']):
        print(f'   Line {idx+1}: {line.strip()[:100]}')

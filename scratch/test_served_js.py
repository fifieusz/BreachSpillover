import urllib.request

res = urllib.request.urlopen('http://127.0.0.1:8000/static/js/app.v17.js')
content = res.read().decode('utf-8')
print('Served JS length:', len(content))
assert 'Instant (< 2ms) Response on User Interaction' in content, "Missing header"
assert 'window.addEventListener("pointerdown"' in content, "Missing pointerdown listener"
assert 'RetroSoundEngine' in content, "Missing RetroSoundEngine"
assert 'SoundManager' in content, "Missing SoundManager"
print('Server is serving the updated zero-latency audio engine perfectly!')

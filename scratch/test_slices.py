import ctypes, time, os

winmm = ctypes.windll.winmm
fpath = os.path.abspath('frontend/static/sounds/Clickingsound.mp3')
winmm.mciSendStringA(f'open "{fpath}" type mpegvideo alias s'.encode('ascii'), None, 0, 0)

buf = ctypes.create_string_buffer(256)
winmm.mciSendStringA(b'status s length', buf, 256, 0)
length_ms = int(buf.value.decode())
print(f"Total length: {length_ms} ms")

# Let's test playing 500ms slices to identify where the sound is!
for start_ms in [0, 200, 500, 1000, 1500, 2000, 2500, 3000, 3500]:
    if start_ms < length_ms:
        print(f"Testing start at {start_ms} ms...")
        winmm.mciSendStringA(f'play s from {start_ms} to {start_ms + 400}'.encode('ascii'), None, 0, 0)
        time.sleep(0.5)

winmm.mciSendStringA(b'close s', None, 0, 0)
print('Finished.')

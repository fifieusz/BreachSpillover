import ctypes
import os

winmm = ctypes.windll.winmm
buf = ctypes.create_string_buffer(256)

for fname in ["Clickingsound.mp3", "Errorsound.mp3", "Exportbuttonsound.mp3", "Searchingsound.mp3"]:
    fpath = os.path.abspath(f"frontend/static/sounds/{fname}")
    cmd_open = f'open "{fpath}" type mpegvideo alias s'.encode('ascii')
    winmm.mciSendStringA(cmd_open, None, 0, 0)
    winmm.mciSendStringA(b'status s length', buf, 256, 0)
    print(f"{fname}: {buf.value.decode()} ms")
    winmm.mciSendStringA(b'close s', None, 0, 0)

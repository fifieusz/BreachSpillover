import ctypes, time, os

winmm = ctypes.windll.winmm
fpath = os.path.abspath('frontend/static/sounds/Clickingsound.mp3')
winmm.mciSendStringA(f'open "{fpath}" type mpegvideo alias s'.encode('ascii'), None, 0, 0)
print('Playing Clickingsound.mp3...')
winmm.mciSendStringA(b'play s from 0', None, 0, 0)
time.sleep(2)
winmm.mciSendStringA(b'close s', None, 0, 0)
print('Done.')

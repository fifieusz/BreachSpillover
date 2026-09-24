import ctypes
from ctypes import wintypes
import os

# Let's decode Clickingsound.mp3 to PCM using Media Foundation SourceReader
# GUID definitions
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8)
    ]

MF_VERSION = 0x0002
MFSTARTUP_NOSOCKET = 0x1

mfplat = ctypes.windll.mfplat
mfreadwrite = ctypes.windll.mfreadwrite
ole32 = ctypes.windll.ole32

ole32.CoInitializeEx(None, 0)
mfplat.MFStartup(MF_VERSION, MFSTARTUP_NOSOCKET)

# Let's see if we can decode or if we can play with MCI starting at various positions
winmm = ctypes.windll.winmm
fpath = os.path.abspath("frontend/static/sounds/Clickingsound.mp3")

# Let's write a python script to parse the MP3 frames and check when audio volume appears
# Even simpler: we can inspect the raw MP3 frame data
with open(fpath, "rb") as f:
    raw = f.read()

print("File size:", len(raw))

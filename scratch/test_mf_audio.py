import ctypes
from ctypes import wintypes
import os

ole32 = ctypes.windll.ole32
mfplat = ctypes.windll.mfplat
mfreadwrite = ctypes.windll.mfreadwrite

ole32.CoInitializeEx(None, 0)
mfplat.MFStartup(0x0002, 1)

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8)
    ]

# MFAudioFormat_PCM: {00000001-0000-0010-8000-00AA00389B71}
MFAudioFormat_PCM = GUID(1, 0, 0x0010, (ctypes.c_ubyte * 8)(0x80, 0x00, 0x00, 0xaa, 0x00, 0x38, 0x9b, 0x71))
MFMediaType_Audio = GUID(0x73647561, 0x0000, 0x0010, (ctypes.c_ubyte * 8)(0x80, 0x00, 0x00, 0xaa, 0x00, 0x38, 0x9b, 0x71))
MF_MT_MAJOR_TYPE = GUID(0x48eba18e, 0xf827, 0x49ed, (ctypes.c_ubyte * 8)(0x85, 0xde, 0x52, 0x5e, 0x07, 0xa2, 0xe0, 0xcf))
MF_MT_SUBTYPE = GUID(0xf7e34c9a, 0x42e8, 0x4714, (ctypes.c_ubyte * 8)(0xb7, 0x4b, 0xcb, 0x29, 0xd7, 0x2c, 0x35, 0xe5))

MF_SOURCE_READER_FIRST_AUDIO_STREAM = 0xFFFFFFFD

class IMFSourceReaderVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("GetStreamSelection", ctypes.c_void_p),
        ("SetStreamSelection", ctypes.c_void_p),
        ("GetNativeMediaType", ctypes.c_void_p),
        ("GetCurrentMediaType", ctypes.c_void_p),
        ("SetCurrentMediaType", ctypes.c_void_p),
    ]

class IMFSourceReader(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(IMFSourceReaderVtbl))]

pReader = ctypes.POINTER(IMFSourceReader)()
abs_path = os.path.abspath("frontend/static/sounds/Clickingsound.mp3")
hr = mfreadwrite.MFCreateSourceReaderFromURL(abs_path, None, ctypes.byref(pReader))

# Let's see: GetNativeMediaType
GetNative_Func = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_void_p))(pReader.contents.lpVtbl.contents.GetNativeMediaType)
pNative = ctypes.c_void_p()
hr = GetNative_Func(pReader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, 0, ctypes.byref(pNative))
print("GetNativeMediaType hr:", hex(hr))

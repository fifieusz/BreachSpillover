import ctypes
from ctypes import wintypes
import os
import struct

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
# MF_MT_MAJOR_TYPE: {48eba18e-f827-49ed-85de-525e07a2e0cf}
MF_MT_MAJOR_TYPE = GUID(0x48eba18e, 0xf827, 0x49ed, (ctypes.c_ubyte * 8)(0x85, 0xde, 0x52, 0x5e, 0x07, 0xa2, 0xe0, 0xcf))
# MFMediaType_Audio: {73647561-0000-0010-8000-00AA00389B71}
MFMediaType_Audio = GUID(0x73647561, 0x0000, 0x0010, (ctypes.c_ubyte * 8)(0x80, 0x00, 0x00, 0xaa, 0x00, 0x38, 0x9b, 0x71))
# MF_MT_SUBTYPE: {f7e34c9a-42e8-4714-b74b-cb29d72c35e5}
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
        ("SetCurrentPosition", ctypes.c_void_p),
        ("ReadSample", ctypes.c_void_p),
        ("Flush", ctypes.c_void_p),
        ("GetServiceForStream", ctypes.c_void_p),
        ("GetPresentationAttribute", ctypes.c_void_p),
    ]

class IMFSourceReader(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(IMFSourceReaderVtbl))]

class IMFMediaTypeVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("GetItem", ctypes.c_void_p),
        ("GetItemType", ctypes.c_void_p),
        ("CompareItem", ctypes.c_void_p),
        ("Compare", ctypes.c_void_p),
        ("GetUINT32", ctypes.c_void_p),
        ("GetUINT64", ctypes.c_void_p),
        ("GetDouble", ctypes.c_void_p),
        ("GetGUID", ctypes.c_void_p),
        ("GetStringLength", ctypes.c_void_p),
        ("GetString", ctypes.c_void_p),
        ("GetAllocatedString", ctypes.c_void_p),
        ("GetBlobSize", ctypes.c_void_p),
        ("GetBlob", ctypes.c_void_p),
        ("GetAllocatedBlob", ctypes.c_void_p),
        ("GetUnknown", ctypes.c_void_p),
        ("SetItem", ctypes.c_void_p),
        ("DeleteItem", ctypes.c_void_p),
        ("DeleteAllItems", ctypes.c_void_p),
        ("SetUINT32", ctypes.c_void_p),
        ("SetUINT64", ctypes.c_void_p),
        ("SetDouble", ctypes.c_void_p),
        ("SetGUID", ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(GUID))),
        ("SetString", ctypes.c_void_p),
        ("SetBlob", ctypes.c_void_p),
        ("SetUnknown", ctypes.c_void_p),
    ]

class IMFMediaType(ctypes.Structure):
    _fields_ = [("lpVtbl", ctypes.POINTER(IMFMediaTypeVtbl))]

pReader = ctypes.POINTER(IMFSourceReader)()
abs_path = os.path.abspath("frontend/static/sounds/Clickingsound.mp3")
hr = mfreadwrite.MFCreateSourceReaderFromURL(abs_path, None, ctypes.byref(pReader))

pMediaType = ctypes.POINTER(IMFMediaType)()
mfplat.MFCreateMediaType(ctypes.byref(pMediaType))

pMediaType.contents.lpVtbl.contents.SetGUID(pMediaType, ctypes.byref(MF_MT_MAJOR_TYPE), ctypes.byref(MFMediaType_Audio))
pMediaType.contents.lpVtbl.contents.SetGUID(pMediaType, ctypes.byref(MF_MT_SUBTYPE), ctypes.byref(MFAudioFormat_PCM))

SetCurrentMediaType_Func = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)(pReader.contents.lpVtbl.contents.SetCurrentMediaType)
hr = SetCurrentMediaType_Func(pReader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, None, pMediaType)
print("SetCurrentMediaType hr:", hex(hr))

# Read samples
ReadSample_Func = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
    ctypes.POINTER(ctypes.c_longlong), ctypes.POINTER(ctypes.c_void_p)
)(pReader.contents.lpVtbl.contents.ReadSample)

all_pcm = bytearray()
stream_flags = ctypes.c_ulong()
actual_stream = ctypes.c_ulong()
timestamp = ctypes.c_longlong()
pSample = ctypes.c_void_p()

# IMFSample ConvertToContiguousBuffer
MF_SOURCE_READERF_ENDOFSTREAM = 0x00000200

# We can query IMFSample buffer
while True:
    hr = ReadSample_Func(pReader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, 0, ctypes.byref(actual_stream), ctypes.byref(stream_flags), ctypes.byref(timestamp), ctypes.byref(pSample))
    if hr != 0 or (stream_flags.value & MF_SOURCE_READERF_ENDOFSTREAM):
        break
    if pSample.value:
        # Get buffer
        pBuffer = ctypes.c_void_p()
        # IMFSample::ConvertToContiguousBuffer is at index 17
        vtbl = ctypes.cast(pSample, ctypes.POINTER(ctypes.c_void_p))
        ConvertToContiguousBuffer_Func = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))(vtbl[17])
        hr = ConvertToContiguousBuffer_Func(pSample, ctypes.byref(pBuffer))
        if hr == 0 and pBuffer.value:
            # IMFMediaBuffer::Lock is at index 3
            buf_vtbl = ctypes.cast(pBuffer, ctypes.POINTER(ctypes.c_void_p))
            Lock_Func = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong))(buf_vtbl[3])
            Unlock_Func = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(buf_vtbl[4])
            pData = ctypes.c_void_p()
            curLen = ctypes.c_ulong()
            hr = Lock_Func(pBuffer, ctypes.byref(pData), None, ctypes.byref(curLen))
            if hr == 0:
                buf_bytes = ctypes.string_at(pData.value, curLen.value)
                all_pcm.extend(buf_bytes)
                Unlock_Func(pBuffer)
            # Release buffer
            ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(buf_vtbl[2])(pBuffer)
        # Release sample
        ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtbl[2])(pSample)

print(f"Decoded PCM total bytes: {len(all_pcm)}")

# Let's inspect the 16-bit PCM samples to find where the click sound actually starts!
samples = struct.unpack(f"<{len(all_pcm)//2}h", all_pcm[:len(all_pcm)-(len(all_pcm)%2)])
print(f"Total 16-bit samples: {len(samples)}")

# Assuming 44100 Hz stereo or mono (let's check sample rate from reader or find non-silent sample)
# Find first sample with amplitude > 500 (silence threshold)
first_sound_idx = None
max_amp = max(abs(s) for s in samples) if samples else 0
print(f"Max amplitude: {max_amp}")

for idx, s in enumerate(samples):
    if abs(s) > 1000:
        first_sound_idx = idx
        break

print(f"First sound index (>1000 amplitude): {first_sound_idx}")
if first_sound_idx is not None:
    # Assuming 44100 Hz stereo (2 samples per sample period = 88200 samples/sec)
    ms_stereo = first_sound_idx / (44100 * 2) * 1000
    ms_mono = first_sound_idx / 44100 * 1000
    print(f"Time of first audible sound: {ms_stereo:.1f}ms (if stereo) or {ms_mono:.1f}ms (if mono)")

import os

sounds = ['Clickingsound.mp3', 'Searchingsound.mp3', 'Errorsound.mp3', 'Exportbuttonsound.mp3']

for name in sounds:
    path = os.path.join('frontend/static/sounds', name)
    with open(path, 'rb') as f:
        data = f.read()
    
    # Check ID3
    id3_len = 0
    if data[:3] == b'ID3':
        id3_len = 10 + ((data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9])
    
    # Count MPEG frames
    pos = id3_len
    frames = 0
    first_sr = 44100
    while pos < len(data) - 4:
        if data[pos] == 0xFF and (data[pos+1] & 0xE0) == 0xE0:
            ver = (data[pos+1] >> 3) & 3
            layer = (data[pos+1] >> 1) & 3
            br_idx = (data[pos+2] >> 4) & 0x0F
            sr_idx = (data[pos+2] >> 2) & 0x03
            pad = (data[pos+2] >> 1) & 1
            br_table = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
            if layer == 1 and br_idx in range(1, 15) and sr_idx in range(3):
                bitrate = br_table[br_idx] * 1000
                sr = 44100 if sr_idx == 0 else (48000 if sr_idx == 1 else 32000)
                first_sr = sr
                flen = (144 * bitrate) // sr + pad
                frames += 1
                pos += flen
                continue
        pos += 1
    
    dur_ms = (frames * 1152 / first_sr) * 1000
    print(f"{name}: size={len(data)}B, id3={id3_len}B, frames={frames}, sr={first_sr}, dur={dur_ms:.1f}ms")

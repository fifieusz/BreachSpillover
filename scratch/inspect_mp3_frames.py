with open('frontend/static/sounds/Clickingsound.mp3', 'rb') as f:
    data = f.read()

idx = 0
frames = []
while idx < len(data) - 4:
    if data[idx] == 0xFF and (data[idx+1] & 0xE0) == 0xE0:
        b1, b2, b3, b4 = data[idx], data[idx+1], data[idx+2], data[idx+3]
        mpeg_version = (b2 >> 3) & 0x03
        layer = (b2 >> 1) & 0x03
        bitrate_idx = (b3 >> 4) & 0x0F
        samplerate_idx = (b3 >> 2) & 0x03
        padding = (b3 >> 1) & 0x01
        
        sr_table = {0: 44100, 1: 48000, 2: 32000}
        br_table = {1:32, 2:40, 3:48, 4:56, 5:64, 6:80, 7:96, 8:112, 9:128, 10:160, 11:192, 12:224, 13:256, 14:320}
        
        if mpeg_version == 3 and layer == 1 and samplerate_idx in sr_table and bitrate_idx in br_table:
            sr = sr_table[samplerate_idx]
            br = br_table[bitrate_idx] * 1000
            frame_len = int(144 * br / sr) + padding
            # In MP3, frame header is 4 bytes.
            # Next is side information (32 bytes for MPEG1 stereo, 17 bytes for mono).
            # Then main_data.
            frames.append((idx, frame_len, br))
            idx += frame_len
            continue
    idx += 1

print(f"Total frames: {len(frames)}")

# In MP3, silent frames have very specific bit allocation:
# In silence, Huffman code bits and main data are mostly empty / zero.
for i, (offset, length, br) in enumerate(frames):
    frame_bytes = data[offset:offset+length]
    # Check entropy / byte diversity
    unique_bytes = len(set(frame_bytes[4:]))
    zero_bytes = frame_bytes[4:].count(0)
    time_ms = i * 1152 / 44100 * 1000
    if i < 30 or unique_bytes > 50:
        print(f"Frame {i:2d} ({time_ms:6.1f}ms): len={length}, unique={unique_bytes}, zeroes={zero_bytes}/{length-4}")

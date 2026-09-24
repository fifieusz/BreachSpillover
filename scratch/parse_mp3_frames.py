with open("frontend/static/sounds/Clickingsound.mp3", "rb") as f:
    data = f.read()

# Skip ID3
pos = 187 # first frame

# Frame 0 is Info tag
frames = []
idx = 0
while pos < len(data) - 4:
    if data[pos] == 0xFF and (data[pos+1] & 0xE0) == 0xE0:
        ver = (data[pos+1] >> 3) & 3
        layer = (data[pos+1] >> 1) & 3
        has_crc = (data[pos+1] & 1) == 0
        br_idx = (data[pos+2] >> 4) & 0x0F
        sr_idx = (data[pos+2] >> 2) & 0x03
        pad = (data[pos+2] >> 1) & 1
        channel_mode = (data[pos+3] >> 6) & 3
        
        br_table = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
        if layer == 1 and br_idx in range(1, 15) and sr_idx in range(3):
            bitrate = br_table[br_idx] * 1000
            sr = 44100 if sr_idx == 0 else (48000 if sr_idx == 1 else 32000)
            flen = (144 * bitrate) // sr + pad
            
            # side info offset
            side_offset = pos + 4 + (2 if has_crc else 0)
            side_len = 32 if channel_mode != 3 else 17
            side = data[side_offset:side_offset+side_len]
            
            frames.append({
                "idx": idx,
                "pos": pos,
                "flen": flen,
                "side": side.hex()
            })
            idx += 1
            pos += flen
            continue
    pos += 1

print(f"Total frames: {len(frames)}")
for f in frames[:20]:
    print(f"Frame {f['idx']}: offset={f['pos']} len={f['flen']} side={f['side']}")

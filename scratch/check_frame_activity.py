with open('frontend/static/sounds/Clickingsound.mp3', 'rb') as f:
    data = f.read()

pos = 187 # after ID3
frame_idx = 0
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
            sr = 44100
            flen = (144 * bitrate) // sr + pad
            
            # Rough energy check: count non-zero bytes in audio payload
            payload = data[pos+36:pos+flen] # skip header + side info
            non_zeros = sum(1 for b in payload if b != 0)
            ratio = non_zeros / len(payload) if len(payload) > 0 else 0
            time_ms = (frame_idx * 1152 / 44100) * 1000
            print(f"Frame {frame_idx:2d} ({time_ms:6.1f}ms): len={flen}, payload_nz={ratio:.2f}")
            
            frame_idx += 1
            pos += flen
            continue
    pos += 1

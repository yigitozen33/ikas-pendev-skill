"""Synthetic home-page screenshots for the axes.py shot test: one layout light and dark, one other layout."""
import os
import struct, sys, zlib
def png(path, w, h, rects, bg):
    px = [[bg] * w for _ in range(h)]
    for x0, y0, x1, y1, c in rects:
        for y in range(y0, y1):
            for x in range(x0, x1): px[y][x] = c
    raw = b"".join(b"\x00" + bytes(v for p in row for v in p) for row in px)
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
L, D, A = (238, 235, 226), (20, 22, 20), (180, 70, 40)
W, H = 480, 600
split = [(0, 0, 480, 30, D), (0, 40, 240, 300, A), (260, 120, 460, 150, D), (260, 170, 400, 190, D), (0, 320, 150, 520, D), (165, 320, 315, 520, D), (330, 320, 480, 520, D)]
inv = [(a, b, c, d, L if col == D else (60, 140, 120)) for a, b, c, d, col in split]
centred = [(0, 0, 480, 30, D), (0, 30, 480, 300, A), (140, 140, 340, 170, L), (190, 190, 290, 210, L), (40, 340, 440, 360, D), (40, 380, 440, 580, D)]
out = sys.argv[1]
png(os.path.join(out, "a.png"), W, H, split, L); png(os.path.join(out, "a-dark.png"), W, H, inv, D); png(os.path.join(out, "b.png"), W, H, centred, L)

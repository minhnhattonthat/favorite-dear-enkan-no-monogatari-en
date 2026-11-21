"""lzss.py: the game's LZSS (Okumura variant) used by *.PSS files and the blocks in GDATA.BIN.

Block layout: u32 LE decompressed size, then the LZSS stream. Flag byte, bits read LSB first: 1 = literal byte,
0 = back-reference of two bytes b0 b1: ring position = b0 | (b1 & 0xF0) << 4, length = (b1 & 0x0F) + 3.
4096-byte ring buffer, zero-filled, write position starts at 0xFEE.

decompress(data, off=0) -> (bytes, end_offset)   end_offset = first byte after the stream
compress(raw) -> bytes                            (with the u32 size header)
"""
N = 4096
F = 18
THRESHOLD = 2
R0 = N - F


def decompress(data, off=0):
    size = int.from_bytes(data[off:off + 4], "little")
    p = off + 4
    ring = bytearray(N)
    r = R0
    out = bytearray()
    flags = 0
    nbits = 0
    while len(out) < size:
        if nbits == 0:
            flags = data[p]
            p += 1
            nbits = 8
        if flags & 1:
            c = data[p]
            p += 1
            out.append(c)
            ring[r] = c
            r = (r + 1) & (N - 1)
        else:
            b0, b1 = data[p], data[p + 1]
            p += 2
            pos = b0 | ((b1 & 0xF0) << 4)
            for k in range((b1 & 0x0F) + THRESHOLD + 1):
                c = ring[(pos + k) & (N - 1)]
                out.append(c)
                ring[r] = c
                r = (r + 1) & (N - 1)
        flags >>= 1
        nbits -= 1
    if len(out) != size:
        raise ValueError(f"overran size {size} by {len(out) - size} at {off:#x}")
    return bytes(out), p


def compress(raw):
    """Greedy LZSS with a ring buffer identical to the decoder's (zero-filled, start 0xFEE)."""
    raw = bytes(raw)
    n = len(raw)
    out = bytearray(n.to_bytes(4, "little"))
    # Virtual stream: N-F zero bytes of ring prefill followed by the data. Ring position of stream index i is
    # (i + R0 - (N - F)) & 0xFFF == i & 0xFFF when prefix length is N-F... compute directly instead.
    buf = bytes(N - F) + raw  # stream index j corresponds to data index j - (N - F); ring pos = (j + R0 - (N-F)) % N
    base = N - F
    heads = {}
    i = 0
    group = bytearray()
    flags = 0
    bit = 0

    def key(j):
        return buf[j:j + 3]

    # index the zero prefill (only last N-F positions matter; one entry suffices for zeros)
    for j in range(max(0, base - (N - F)), base):
        heads.setdefault(key(j), []).append(j)
    while i < n:
        j = base + i
        best_len, best_pos = 0, 0
        maxlen = min(F, n - i)
        if maxlen >= 3:
            cands = heads.get(key(j), [])
            # keep window: candidates within the last N - F bytes (so the ring slot is not overwritten mid-copy)
            lo = j - (N - F)
            for c in reversed(cands[-64:]):
                if c < lo:
                    break
                L = 0
                while L < maxlen and buf[c + L] == buf[j + L]:
                    L += 1
                if L > best_len:
                    best_len, best_pos = L, c
                    if L == maxlen:
                        break
        if best_len >= 3:
            ringpos = (best_pos - base + R0) & (N - 1)
            group += bytes([ringpos & 0xFF, ((ringpos >> 4) & 0xF0) | (best_len - 3)])
            step = best_len
        else:
            flags |= 1 << bit
            group.append(raw[i])
            step = 1
        for k in range(step):
            heads.setdefault(key(j + k), []).append(j + k)
        i += step
        bit += 1
        if bit == 8:
            out.append(flags)
            out += group
            group = bytearray()
            flags = 0
            bit = 0
    if bit:
        out.append(flags)
        out += group
    return bytes(out)


def compress_optimal(raw, cands=256):
    """LZSS with an optimal parse (literal = 9 bits, match = 17 bits, shortest stream over every split): ~4% smaller
    than compress(), for files that must stay within their sectors (TITLE/*.PSS)."""
    raw = bytes(raw)
    n = len(raw)
    base = N - F
    buf = bytes(base) + raw
    heads = {}
    for j in range(0, base):
        heads.setdefault(buf[j:j + 3], []).append(j)
    best = [(0, 0)] * n  # (longest match length, its stream position) at each data index
    for i in range(n):
        j = base + i
        maxlen = min(F, n - i)
        if maxlen >= 3:
            bl, bp = 0, 0
            lo = j - (N - F)
            for c in reversed(heads.get(buf[j:j + 3], [])[-cands:]):
                if c < lo:
                    break
                L = 0
                while L < maxlen and buf[c + L] == buf[j + L]:
                    L += 1
                if L > bl:
                    bl, bp = L, c
                    if L == maxlen:
                        break
            best[i] = (bl, bp)
        heads.setdefault(buf[j:j + 3], []).append(j)
    cost = [0] * (n + 1)
    step = [1] * n
    for i in range(n - 1, -1, -1):
        cost[i], step[i] = 9 + cost[i + 1], 1
        for L in range(3, best[i][0] + 1):
            if 17 + cost[i + L] < cost[i]:
                cost[i], step[i] = 17 + cost[i + L], L
    out = bytearray(n.to_bytes(4, "little"))
    group, flags, bit, i = bytearray(), 0, 0, 0
    while i < n:
        if step[i] == 1:
            flags |= 1 << bit
            group.append(raw[i])
        else:
            ringpos = (best[i][1] - base + R0) & (N - 1)
            group += bytes([ringpos & 0xFF, ((ringpos >> 4) & 0xF0) | (step[i] - 3)])
        i += step[i]
        bit += 1
        if bit == 8:
            out.append(flags)
            out += group
            group, flags, bit = bytearray(), 0, 0
    if bit:
        out.append(flags)
        out += group
    return bytes(out)


if __name__ == "__main__":
    import sys
    d = open(sys.argv[1], "rb").read()
    off = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0
    raw, end = decompress(d, off)
    print(f"size {len(raw)} stream end {end:#x}")
    if len(sys.argv) > 3:
        open(sys.argv[3], "wb").write(raw)

"""evscript.py: parse the GDATA event-script files (docs/re/events.md) into ops, messages and text segments.

    python -X utf8 tools/evscript.py check              sweep every script file; exit 1 if any fails to parse
    python -X utf8 tools/evscript.py dump SECTOR        ops and messages of one file (sector in hex, as in `files()`)

File layout (verified: the step loop 0x800C8BB0 reads it; every file sweeps end to end, tests/test_extract.py):
    u16 argtab   byte offset of the argument-count table (always 6)
    u16 vars     byte offset of the symbol/variable area (0x1D2, 0x1AE, ...)
    u16 code     byte offset of the code; pc counts halfwords from here
    argtab..vars u16 per opcode: number of argument words (the VM advances pc by 1 + count)
Code: pc 0 is normally `0x28 <goto>` over a data area of variable slots. Opcodes < len(argtab) are VM ops
(0x28 goto, 0x29 call, 0x2A return, 0x37 end, >= 0x3B the jump table at 0x80039108). An argument with bit 15 set
is a reference: (arg & 0x7FFF) is a code halfword index (a variable slot, a label, or a message).
Messages sit inline between ops and are reached only by reference (op 0x3C and friends), never by fall-through.
A message is a printer stream (printer 0x800CC9EC): font codes < 0x66C and 0xFFxx codes with PRINTER_ARGS argument
words, ended by 0xFFFF. 0xFFE0 0xFFE0 after an 0xFFFF is padding. A reference may land inside a message (several
entry points share one tail), so text is cut into segments at every reference target.
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gdata  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NCODES = gdata.NCODES  # 0x6F0 in this game (game 1: 0x66C)
EN_LO = 0x2020  # English pair glyphs 0x2020-0xFEFF (tools/en.py): text in built scripts, never an opcode
# 0xFFxx -> argument words, from the printer's compare chain at 0x800CCB50 (each handler's pc increments).
# 0xFFFB is not in that chain; every message starts `FFFB 8xxx` or `FFE0 xxxx`, so it takes one word like 0xFFE0.
# 0xFFFC (no handler there) occurs alone inside text and as the last word of a file.
PRINTER_ARGS = {
    0xFFC0: 1, 0xFFC1: 1, 0xFFE0: 1, 0xFFE5: 1, 0xFFE6: 0, 0xFFE7: 1, 0xFFE8: 1, 0xFFE9: 1, 0xFFEA: 1, 0xFFEB: 0,
    0xFFEC: 0, 0xFFED: 0, 0xFFEE: 1, 0xFFF0: 0, 0xFFF1: 1, 0xFFF2: 0, 0xFFF3: 0, 0xFFF4: 1, 0xFFF5: 1, 0xFFF6: 2,
    0xFFF7: 1, 0xFFF8: 1, 0xFFF9: 2, 0xFFFA: 1, 0xFFFB: 1, 0xFFFC: 0, 0xFFFD: 3, 0xFFFE: 3, 0xFFFF: 0,
}
PAD = (0xFFE0, 0xFFE0)
# (opcode, argument index) whose reference is a message (show-message ops; from the original scripts: 1588 targets
# of 0x3C arg 0 are message starts or inside messages, and every one the first sweep called an op parses as text).
MSG_REFS = {(0x3C, 0), (0x3D, 2), (0x3D, 4), (0x90, 1), (0xD5, 1), (0xDE, 1)}


class ParseError(ValueError):
    pass


class Script:
    """One event-script file. Offsets in `items`/`segments` are code halfword indices (pc values)."""

    def __init__(self, data):
        self.data = data
        self.argtab, self.vars, self.code_off = struct.unpack_from("<3H", data)
        ntab = (self.vars - self.argtab) // 2
        self.tab = struct.unpack_from("<%dH" % ntab, data, self.argtab)
        self.code = struct.unpack_from("<%dH" % ((len(data) - self.code_off) // 2), data, self.code_off)
        n = len(self.code)
        while n and self.code[n - 1] == 0:
            n -= 1
        self.n = n  # used halfwords; the rest is zero padding to the sector
        self.start = self.code[1] & 0x7FFF if self.code[0] == 0x28 else 0  # first op after the variable area
        self.tokens = set()  # pc of every token start inside messages
        self.items = self._sweep()
        self.refs = self._refs()
        # A message may start with a glyph below the opcode count, which the first sweep reads as an op. Re-sweep
        # until stable: a target of a show-message argument (MSG_REFS) is a message; so is an untargeted word right
        # after a message that parses as one (code after a message is reached only by a reference).
        for _ in range(8):
            self.tokens = set()
            msg_t = {t for op, i, t in self.refs if (self.code[op], i) in MSG_REFS}
            items = self._sweep({t for _, _, t in self.refs}, msg_t)
            if items == self.items:
                break
            self.items = items
            self.refs = self._refs()
        self.segments = self._segments()

    def byte(self, pc):
        """file byte offset of code halfword pc"""
        return self.code_off + 2 * pc

    def _text_end(self, j):
        code, n = self.code, self.n
        while j < n:
            self.tokens.add(j)
            v = code[j]
            if v == 0xFFFF:
                return j + 1
            if v >= 0xFF00:
                if v not in PRINTER_ARGS:
                    raise ParseError(f"pc {j:#x}: unknown printer code {v:04X}")
                j += 1 + PRINTER_ARGS[v]
            elif v < NCODES or EN_LO <= v:
                j += 1
            else:
                raise ParseError(f"pc {j:#x}: {v:04X} is neither a font code nor a printer code")
        return n  # the last message of a file may run to the end without 0xFFFF

    def _as_message(self, pc):
        """end of a whole message starting at pc (valid codes up to an 0xFFFF), else None; leaves tokens alone"""
        saved = set(self.tokens)
        try:
            end = self._text_end(pc)
            ok = self.code[end - 1] == 0xFFFF
        except ParseError:
            ok = False
        self.tokens = saved
        return end if ok else None

    def _sweep(self, targets=None, msg_targets=()):
        """[(kind, start, end)] covering code[start:n]; kind = 'op' | 'msg' | 'pad'. With `targets` (all reference
        targets) and `msg_targets` (show-message targets), a word there that parses as a whole message is one."""
        code, tab, n = self.code, self.tab, self.n
        pc, items = self.start, []
        while pc < n:
            op = code[pc]
            after_msg = items and items[-1][0] in ("msg", "pad")
            if (op >= 0xFF00 or len(tab) <= op < NCODES or op >= EN_LO
                    or (pc in msg_targets and self._as_message(pc))
                    or (targets is not None and after_msg and pc not in targets and op < NCODES
                        and self._as_message(pc))):
                end = self._text_end(pc)
                items.append(("msg", pc, end))
                pc = end
                if code[pc - 1] == 0xFFFF and code[pc:pc + 2] == PAD:
                    items.append(("pad", pc, pc + 2))
                    pc += 2
                continue
            if op >= len(tab):
                raise ParseError(f"pc {pc:#x}: opcode {op:04X} outside the {len(tab)}-entry argument table")
            items.append(("op", pc, pc + 1 + tab[op]))
            pc += 1 + tab[op]
        if pc != n:
            raise ParseError(f"last op runs past the end ({pc:#x} > {n:#x})")
        return items

    def _refs(self):
        """[(pc of the op, arg index, target pc)] for op arguments with bit 15 set that point into the code."""
        out = []
        for kind, s, e in self.items:
            if kind == "op":
                for i, a in enumerate(self.code[s + 1:e]):
                    if a & 0x8000 and (a & 0x7FFF) < self.n:
                        out.append((s, i, a & 0x7FFF))
        if self.code[0] == 0x28:
            out.append((0, 0, self.start))
        return out

    def _segments(self):
        """[(start, end)] text pieces: each message cut at every reference target inside it."""
        targets = {t for _, _, t in self.refs}
        out = []
        for kind, s, e in self.items:
            if kind != "msg":
                continue
            cuts = sorted({s, *(t for t in targets if s < t < e)})
            for t in cuts:
                if t not in self.tokens:
                    raise ParseError(f"reference to pc {t:#x} lands inside a printer code's arguments")
            for a, b in zip(cuts, cuts[1:] + [e]):
                out.append((a, b))
        return out

    def seg_bytes(self, seg):
        a, b = seg
        return self.data[self.byte(a):self.byte(b)]


def script_files(disc):
    """[(sector, size, data, where)] every event script in GDATA: the directory entries whose header is a script's
    (gdata.kind). Sizes are whole sectors (the directory stores sector counts); `where` = 'entry N'."""
    out = [(sec, cnt * 2048, data, f"entry {i}") for i, sec, cnt, kd, data in gdata.entries(disc) if kd == "script"]
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "dump"])
    ap.add_argument("sector", nargs="?")
    ap.add_argument("--disc", default=str(ROOT / "work/disc/tree"))
    a = ap.parse_args()
    files = script_files(a.disc)
    if a.cmd == "check":
        bad = 0
        nseg = 0
        for sec, size, data, where in files:
            try:
                nseg += len(Script(data).segments)
            except ParseError as e:
                bad += 1
                print(f"{sec:#x} {where}: {e}")
        print(f"{len(files)} files, {bad} failed, {nseg} text segments")
        sys.exit(1 if bad else 0)
    sec = int(a.sector, 16)
    data = next(d for s, _, d, _ in files if s == sec)
    sc = Script(data)
    for kind, s, e in sc.items:
        print(f"{s:04X} {kind:3} " + " ".join("%04X" % v for v in sc.code[s:e]))


if __name__ == "__main__":
    main()

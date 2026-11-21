# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

**Read first:** this game is an expanded re-release of game 1, `../favorite-dear-en` (finished and published): same
engine, same disc layout, most data byte-identical, 56% of the event text verbatim game 1's. Its `docs/re/*.md`,
tools, glossary, translations and graphics redraws are the starting point for every phase; the files here record
only what differs and what was re-verified.

| File | Covers | State |
|---|---|---|
| `disc.md` | files vs game 1, GDATA/SDATA u16 directory, LZSS / uncompressed PSS | directory verified (`tests/test_recon.py`); identity rebuild not tried |
| `text.md` | encoding (font layout, MSB-first bits, NCODES 0x6F0), printer addresses, event scripts (568, all parse), EXE strings (PSX.EXE + OMK.EXE), credits in FIN.EXE, load buffer | encoding + script grammar verified; EXE pointer map open (phase 4) |
| `graphics.md` | graphics-text survey: game 1's sources mapped here, new images looked at | complete for GDATA/root images; OMK modes, e151, e388-e394 open |
| `space.md` | buffer limits, zero runs | candidates |

Prior work: game 1 `../favorite-dear-en` and game 2 `../favorite-dear-junpaku-no-yogensha-en` (different engine,
LKF archives; its glossary/style carry over). No earlier fan patch for this game known (not searched on the web
this session: the owner pointed at the two sister projects).

Helpers: `tools/gdata.py` (directory, kinds, text estimate), `tools/evscript.py` (game 1's script parser), `tools/font.py`
/ `fontmatch.py` / `mktbl.py` (font sheet, MS Gothic match, `tbl/jp.tbl`), `tools/scantext.py` (FFFF string scan),
`tools/gfxmap.py` (game 1 graphics sources here + new images), `tools/tim.py`, `tools/lzss.py`, `tools/retools.py`
(MIPS disassembly, xrefs).

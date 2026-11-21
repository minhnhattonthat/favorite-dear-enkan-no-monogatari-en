# Disc layout

Unpack (verified 2026-11-21): `tools/mkpsxiso/mkpsxiso-2.30-win64/dumpsxiso.exe -x work/disc/tree -s work/disc/layout.xml "rom/Favorite Dear - Enkan no Monogatari (Japan).bin"`
(one MODE2/2352 data track; `license_data.dat` = licence sectors). Identity rebuild (verified 2026-11-21):
`tools/build.py --identity` runs mkpsxiso v2.30 on a copy of `work/disc/layout.xml` with absolute paths and gives a
.bin byte-identical to the original (639,219,504 bytes, sha1 = `rom.sha1`) in ~3 s, with no differences to explain
(EDC/ECC, padding, dates all reproduced); `tests/test_build.py`. Edited files go in through `source=` on their
`<file>` element; a one-byte edit to SYSTEM.CNF changes exactly one sector.

**This game is an expanded re-release of game 1** (`../favorite-dear-en`, PS1 1998): same engine, same disc layout
(PSX.EXE + GDATA.BIN + SDATA.BIN + XAPACK1.XA, `_LOADE.EXE` chain loader), most media byte-identical. Compared file by
file with game 1's tree (2026-11-21):

| File | vs game 1 | What |
|---|---|---|
| SYSTEM.CNF -> SLPS_032.86 | new (40 KB loader, no game text) | boot loader, chains `_LOADE.EXE` / PSX.EXE (game 1: SLPS_01.759) |
| PSX.EXE (1.6 MB, t_addr 0x80010000) | changed | main game: code, 12x12 font, EXE strings, GDATA/SDATA directories |
| OMK.EXE (1.6 MB) | new | a second build of the main game ("Omake" mode from the title, TTL_COM.PSS): **the same 952 EXE strings** as PSX.EXE at other offsets (`scantext.py`), so every EXE text edit has two sites |
| GDATA.BIN (88.5 MB) | changed | graphics + event scripts; 39,543 of 43,233 sectors also occur in game 1's GDATA |
| SDATA.BIN | changed | sound (VAB "pBAV" ...) |
| FD_BALL.EXE, GOVER.EXE, PS_MOV.EXE, TITLE/EPILOG.EXE, TITLE/FD_MOV.EXE, DATA/FIN.EXE, _LOADE.EXE | changed | mini-game, game over, movie player, epilogue, title movie, credits, loader |
| DATA/STAFF.TXT | **gone** | credits text now inside DATA/FIN.EXE (`text.md` §Credits) |
| DATA/01-13.TIM, FONTCLUT.TIM | same | credits pictures; DATA/14.TIM new (a picture, no text) |
| *.STR (OP, DEMO, ENDING, NEIC, SOFIX1) | same | FMV, byte-identical to game 1 |
| TITLE.PSS, NECLOGO*.PSS, NOWLOAD.PSS, OPM1.PSS, TITLE/TTL_{BACK,BALL,CHR,CHR2,INFO,OPT,OPT2}.PSS, EPI_OBJ.PSS | same | images (LZSS) |
| TITLE/TTL_COM.PSS | changed, **uncompressed** | title menu (English: New Game / Load Game / Option / Omake / Visual CG / Mini Event) |
| TITLE/TTL_LOG0.PSS, TTL_LOG1.PSS, STS_OPT2.PSS, NOWLOAD.TIM | new / changed | title logo with the 円環の物語 kanji subtitle (`graphics.md`) |
| XAPACK1.XA (373 MB), DATA/FINA_BGM.XA | changed / same | XA voice and music; guess: the ~30 `(u16, u16)` tables from PSX.EXE 0x1713A8 that each start at 0 index XA tracks (not mapped) |
| DUMMY.BIN | same | 27 MB padding |
| COPY.TXT | new | "(C)2001,1999 NEC Interchannel,Ltd. (C)SOFIX" |

## GDATA / SDATA directory (verified 2026-11-21: `tools/gdata.py`, `tests/test_recon.py`)

Game 1 used `(u32 sector, u32 byte size)` tables at PSX.EXE 0x4C50.. . This game has **one array of
`(u16 sector, u16 sector count)`** per data file:
- GDATA.BIN: PSX.EXE 0x170244 (RAM 0x8017FA44), 965 entries, ends at 0x171158. Entry order is not sector order. It
  covers every GDATA sector except three holes (0x2D90-0x2DDC, 0x3690-0x3692, 0x39A1-0x39A3). **Entry indices 0-~380
  are game 1's directory indices** (game 1 e008 = this e008 ... e243; `tools/gfxmap.py`), so game 1's notes by
  entry number carry over. Kinds: 568 event scripts, 195 TIMs, 204 other (LZSS images, maps, 3D, battle data), 2
  empty. Entry 382 is one 0x64F0-sector span holding the event pictures (TIMs found by sector scan, as in game 1).
- SDATA.BIN: PSX.EXE 0x1700E4, 88 entries, tiles the file exactly.
- OMK.EXE holds its own copy of the GDATA directory at 0x16EA04 (the same sector sequence; guess: same 965 entries).
- Sizes are whole sectors; exact byte lengths are not stored. A file that grows past its sector count needs the
  following entries moved and this directory (both EXEs) rewritten.

## LZSS (game 1's `tools/lzss.py`, copied; same format)

u32 decompressed size, then Okumura LZSS (flag byte LSB first, 1 = literal; ref `pos = b0 | (b1 & 0xF0) << 4`,
`len = (b1 & 0x0F) + 3`, 4096 ring, start 0xFEE). TITLE/TTL_COM.PSS and TTL_LOG0.PSS are stored **uncompressed**
with the same 12-byte image header (u32 size = file size, u16 x, u16 y, u16 width in halfwords, u16 height);
TTL_LOG1.PSS (12 KB, header says 0x1000C) did not parse either way: open.

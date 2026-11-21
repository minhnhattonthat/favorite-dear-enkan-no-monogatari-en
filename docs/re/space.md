# Space and buffer limits (phase 1 candidates; nothing here is verified free)

- **Event-script load buffer** (verified by disassembly, `text.md`): RAM 0x80148CBC, ~0x7000 bytes (zero run PSX.EXE
  0x139456-0x1404BE). Largest original script uses 0x6C78. English that grows a script past it needs game 1's
  answer: pair glyphs (two Latin letters per 16-bit code, `../favorite-dear-en` `tools/en.py`, `asm/font.asm`) and/or
  a bigger buffer. Decide in phase 5.
- **GDATA growth**: the directory stores whole sectors (`disc.md`); a grown script either fits its own sector
  padding or moves later entries (rewrite both directories, PSX.EXE 0x170244 and OMK.EXE 0x16EA04).
- **Zero runs in PSX.EXE** (>= 4 KB; most are BSS-style buffers the game writes at run time: test before use):
  0x142DE9-0x143E54 (4 KB), 0x148754-0x14CAD8 (17 KB), 0x151DC8-0x16F654 (118 KB, RAM 0x801615C8.., heavily referenced:
  not free), 0x178280-0x17E45B (25 KB), 0x1800FC-0x1813D4, 0x18326C-0x184554, 0x185E24-0x189EE0 (16 KB).
- **Font hook space (phase 5, verified by run-time watch):** game 1's free run (0x80124E5D) does not exist here (that
  data was reused). The hook + 6x12 font + scratch (`asm/font.asm`, ~1.7 KB) live at **RAM 0x80192A6C-0x80193D2C**
  (PSX.EXE file 0x18326C, a zero run with no static reference); in OMK.EXE the same run sits at 0x8019122C (-0x1840,
  matched by the bytes after it). `tools/debug/freewatch.lua` (write watch, BIOS and `_LOADE.EXE` reloads of the EXE
  ignored) over title, week1, myh16, hub_ability, battle_castle, hub_save_list: no game write to it. RAM dumps of
  the hub after a memory-card load (`work/qa/p5/qa1dbg/hub/ram_*.bin`) confirm it: the run matches the built EXE
  except the hook's 288-byte scratch (0x8019303C..).
- **0x801956D0-0x80197AD0 is NOT free** although freewatch saw no CPU write: after a memory-card load (the `hub`
  warp) it holds other data (3,479 of 9,216 bytes differ by frame 9000), so something the write watch can't see
  (DMA) fills it. A lesson for every freewatch result: confirm with a RAM dump against the built file.
- English name entry (`asm/name.inc`, phase 8, PSX.EXE only): `insert.NAME_SPACE` 0x80193600-0x80193800 (REPOINT
  shrunk to end there; its strings used up to 0x8019350E).
- Grown EXE strings (`insert.REPOINT`, phase 7) use 0x80193200-0x80193600 (was ..0x80193800) of the same run, past the hook's scratch
  (ends 0x8019315C); the hook's FREE_END is now 0x80193200, so armips refuses a hook that would run into it.
- **OMK.EXE copy verified (2026-11-22, phase 8):** `warp.py omake_mini --lua probes/ramdump.lua --var
  RAM_EVERY=4000` on the English build (`work/qa/p8/omkram/`, arrived f11589): at f12000 and f16000 RAM
  0x8019122C-0x801924EC (hook, font, scratch, repoint 0x801919C0-0x80191FC0, QA tail) equals the built OMK.EXE byte
  for byte (f8000 is still PSX.EXE's context).
- QA string overrides (`build.py --qa ID=text`) use the tail of the hook run, 0x80193800-0x80193D2C. Written at run time (not free): 0x80152628.. (pc 0x8003C564), 0x80158150..
  (0x800D6728), 0x80187A80.. (0x8010312C, 0x800DBB90). `_LOADE.EXE` (0x801C0000, pc 0x801C46B0) re-reads PSX.EXE
  sectors, so data placed in the file is restored on every reload.
- **EPILOG.EXE**: no free space proven inside its image; `asm/epilog.asm` grows the file one sector (game 1's way) and
  copies the hook to 0x80170000 (game 1's address). Verified by RAM dump (2026-11-22): the 1,366-byte blob is
  intact at f12000/16000/20000 of endings 1, 12 and 26 (`work/qa/p5/epi/*/ram_*.bin`).
- EXE strings: in place, 4-byte padded as in game 1 (guess); OMK.EXE has the same strings, so any relocation is done
  twice.

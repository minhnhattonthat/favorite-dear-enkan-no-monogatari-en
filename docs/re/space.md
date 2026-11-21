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
- **Font space**: the 12x12 font ends at 0x6EF; game 1 put its English pair-glyph cells and code over unused space it
  proved free. Re-find here in phase 5.
- EXE strings: in place, 4-byte padded as in game 1 (guess); OMK.EXE has the same strings, so any relocation is done
  twice.

; name.asm: English name entry, PSX.EXE only (asm/name.inc; the new-game name entry runs only there).
; armips, run by tools/insert.py:
;   armips asm/name.asm -strequ EXE_IN <exe> -strequ EXE_OUT <out> -equ NAME_FREE <a> -equ NAME_FREE_END <b>
; NAME_FREE..NAME_FREE_END = insert.NAME_SPACE, the tail of the verified free run past insert.REPOINT (space.md).

.psx
.open EXE_IN, EXE_OUT, 0x8000F800
.include "name.inc"
.close

; skill.asm: hero status screen skill names in the main font, PSX.EXE only (asm/skill.inc).
; armips, run by tools/insert.py:
;   armips asm/skill.asm -strequ EXE_IN <exe> -strequ EXE_OUT <out>

.psx
.open EXE_IN, EXE_OUT, 0x8000F800
.include "skill.inc"
.include "gift.inc"                ; hero visit GIFT: stat window and prompt pieces
.close

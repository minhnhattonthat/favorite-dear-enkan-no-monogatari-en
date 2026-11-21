; btname.asm: English battle name plates in PSX.EXE (battles run only there; OMK.EXE has no battle code).
; armips, run by tools/insert.py:
;   armips asm/btname.asm -strequ EXE_IN <exe> -strequ EXE_OUT <out> -strequ BTFONT_BIN <f> -strequ BTHERO_BIN <h>
;                         -strequ BTENEMY_BIN <e>          (data: tools/btname.py from trans/btname.tsv)

.psx
.open EXE_IN, EXE_OUT, 0x8000F800
.include "btname.inc"
.close

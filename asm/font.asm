; font.asm: English pair glyphs in PSX.EXE and OMK.EXE (docs/re/text.md §English). armips, run by tools/insert.py:
;   armips asm/font.asm -strequ EXE_IN <exe> -strequ EXE_OUT <out> -strequ FONT_BIN <en6x12.bin>
;                       -equ GLYPH <glyph fetch> -equ FREE <free run> -equ FREE_END <its end>
;
; GLYPH (PSX.EXE 0x800D6BB4, OMK.EXE 0x800D976C; game 1 0x800FDCA8) renders font cell `code` (a1) from a 1bpp image
; (a0, 24-byte rows, MSB-first) into a 2bpp buffer (a2). Every printer path (event scripts, EXE strings, menus) goes
; through it. Its first two instructions are game 1's (addiu sp,-0x40 / sw s7,0x34(sp)), redone in pair_orig.
; FREE..FREE_END: a zero run of the EXE that nothing writes at run time (docs/re/space.md, tools/debug/freewatch.lua).

.psx
.open EXE_IN, EXE_OUT, 0x8000F800

.org GLYPH
    j       pair_hook
    nop                            ; replaced: addiu sp,-0x40 / sw s7,0x34(sp) (redone in pair_orig)

.org FREE
.include "pair.inc"
pair_orig:
    addiu   sp, sp, -0x40
    j       GLYPH + 8
    sw      s7, 0x34(sp)
.include "pair_data.inc"
pair_end:

.if pair_end > FREE_END
    .error "font hook overflows its free run (docs/re/space.md)"
.endif

.close

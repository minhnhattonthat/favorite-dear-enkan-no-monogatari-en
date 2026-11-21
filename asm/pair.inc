; pair.inc: the pair-glyph hook body shared by asm/font.asm (PSX.EXE, OMK.EXE) and asm/epilog.asm (EPILOG.EXE).
; Game 1's (../favorite-dear-en/asm/pair.inc) with this game's bit order: the font is MSB-first (bit 7 = leftmost
; pixel, docs/re/text.md §Font).
; The renderers take a1 = font cell code (row = code >> 4, column = code & 15, 12x12 cells), a0 = 1bpp image with
; 24-byte rows. Codes 0x2020-0xFEFF are two English letters (low byte left, high byte right): their 6x12 glyphs
; (pair_font, bits 7..2 of each row byte, tools/font_en.py) go into cell 0 of `pair_scratch` as
; byte 0 = left | right >> 6, byte 1 = right << 2, and the renderer runs on that instead (a0 = pair_scratch, a1 = 0).
; Codes below 0x2000 fall through unchanged. The includer defines `pair_orig` (the displaced instructions + jump
; back) right after this body, and includes pair_data.inc (font + scratch) somewhere it can.

pair_hook:
    andi    t0, a1, 0xFFFF
    sltiu   t1, t0, 0x2000
    bnez    t1, pair_orig
    nop
    li      t2, pair_scratch
    andi    t3, t0, 0xFF           ; left letter
    srl     t4, t0, 8              ; right letter
    addiu   t3, t3, -0x20
    addiu   t4, t4, -0x20
    sll     t5, t3, 1              ; *12 = (*2 + *1) * 4
    addu    t3, t5, t3
    sll     t3, t3, 2
    sll     t5, t4, 1
    addu    t4, t5, t4
    sll     t4, t4, 2
    li      t5, pair_font
    addu    t3, t3, t5
    addu    t4, t4, t5
    li      t6, 12
@@row:
    lbu     t7, 0(t3)
    lbu     t8, 0(t4)
    addiu   t3, t3, 1
    srl     t9, t8, 6
    or      t7, t7, t9
    sb      t7, 0(t2)
    sll     t8, t8, 2
    sb      t8, 1(t2)              ; low byte only
    addiu   t2, t2, 24             ; next scratch row
    addiu   t6, t6, -1
    bnez    t6, @@row
    addiu   t4, t4, 1
    li      a0, pair_scratch
    move    a1, zero

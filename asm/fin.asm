; fin.asm: English pair glyphs in DATA/FIN.EXE, the staff roll (docs/re/text.md §Credits). Game 1's hook
; (../favorite-dear-en asm/fin.asm) with this disc's addresses. armips, run by tools/insert.py:
;   armips asm/fin.asm -strequ EXE_IN <FIN.EXE> -strequ EXE_OUT <out> -strequ FONT_BIN <fin font>
;
; 0x80013CE8 glyph_addr(a0 = pointer to a double-byte code) returns the address of its 22-byte glyph (11 rows, u16
; big-endian, bit 15 = leftmost pixel); game 1 0x80013BD0, the same 0x88 bytes of code. FIN draws a double-byte code
; when the lead byte is 0x81-0x9F or 0xE0-0xFC (0x8001202C, byte-identical to game 1's 0x80011F1C); its font stops
; at 0x9872, so leads 0xE0-0xFC are free. They carry two English letters:
;   n = (lead - 0xE0) * 189 + (trail - 0x40),  left = n / 74,  right = n % 74   (indexes into font_en.FIN_CHARSET)
; The hook ORs the two 6-px letters (left into bits 15-10, right into bits 9-4) into a scratch glyph and returns it.
; Code, font and scratch overwrite the Cyrillic and box-drawing glyphs (SJIS 0x8440-0x84BE, glyph indexes 426-523
; of the table at 0x8002063C; kanji start at 0x80023344), which the roll never uses (tests/test_fin.py).

.psx
.open EXE_IN, EXE_OUT, 0x8000F800

GLYPH_ADDR equ 0x80013CE8
FREE       equ 0x80022AD8          ; glyph 426 (Cyrillic А) = 0x8002063C + 22 * 426
FREE_END   equ 0x80023344          ; glyph 524 (first kanji)
NCHARS     equ 74

.org GLYPH_ADDR
    j       fin_hook
    nop                            ; replaced: addiu sp,-0x18 / sw ra,0x14(sp) (redone in fin_orig)

.org FREE
fin_hook:
    lbu     t0, 0(a0)
    lbu     t1, 1(a0)
    sltiu   t2, t0, 0xE0
    bnez    t2, fin_orig
    addiu   t0, t0, -0xE0
    li      t2, 189
    multu   t0, t2
    mflo    t0
    addiu   t1, t1, -0x40
    addu    t0, t0, t1             ; n
    li      t2, NCHARS
    divu    t0, t2
    mflo    t3                     ; left letter
    mfhi    t4                     ; right letter
    sll     t5, t3, 3              ; *11 = *8 + *2 + *1
    sll     t6, t3, 1
    addu    t5, t5, t6
    addu    t3, t5, t3
    sll     t5, t4, 3
    sll     t6, t4, 1
    addu    t5, t5, t6
    addu    t4, t5, t4
    li      t5, fin_font
    addu    t3, t3, t5
    addu    t4, t4, t5
    li      v0, fin_scratch
    move    t2, v0
    li      t6, 11
@@row:
    lbu     t7, 0(t3)
    lbu     t8, 0(t4)
    sll     t7, t7, 10
    sll     t8, t8, 4
    or      t7, t7, t8
    srl     t8, t7, 8
    sb      t8, 0(t2)              ; big-endian u16
    sb      t7, 1(t2)
    addiu   t3, t3, 1
    addiu   t4, t4, 1
    addiu   t6, t6, -1
    bnez    t6, @@row
    addiu   t2, t2, 2
    jr      ra
    nop

fin_orig:
    addiu   sp, sp, -0x18
    j       GLYPH_ADDR + 8
    sw      ra, 0x14(sp)

fin_scratch:
    .fill 22, 0
fin_font:                          ; 11 bytes per letter, bit 5 = leftmost pixel (font_en.fin_binary)
    .incbin FONT_BIN
fin_end:

.if fin_end > FREE_END
    .error "FIN hook overflows the Cyrillic/box-drawing glyphs into the kanji"
.endif

.close

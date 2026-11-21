; btname.inc: English battle name plates (docs/re/graphics.md §Battle name plates; data from tools/btname.py).
;
; Game 1's (../favorite-dear-en/asm/btname.inc), every address re-found here by tools/codefind.py (game 1 in
; brackets): the routine 0x8001A680-0x8001A840 [0x80042448-0x80042608], same instructions with only addresses moved.
; 0x8001A680 built each unit's 64x8 name label in VRAM by MoveImage-ing
; 8 cells of the 8x8 kana font (bt_font1-3.pss at VRAM 320/384/448,240) to x 0x1E0 + (slot&1)*16, y 0x40 +
; (slot>>1)*8. Names were 8 one-byte font codes: heroes at the start of the record 0x80120FE8[hero id] points
; to, enemies at 0x80115C64 + type*8 (type = u16 at 0x8015D764 + (slot-3)*2). This routine replaces it in place:
; it renders the English name (upper case ASCII, NUL-terminated, at most 15 letters: tools/btname.py check,
; proportional caps4x7 glyphs with 1-px gaps, ink = colour 1 like the kana) into a 4bpp RAM buffer and LoadImages
; that to the same label.
;
; Space: the old enemy table (254 x 8 bytes; the guard below keeps to its first 0x648) holds the font, hero names and the buffer; the enemy names (16 bytes
; each) go over the descriptors of font codes 0x25-0xBF (the kana; a read watch over a whole battle saw no reads
; there in game 1, while the HUD reads codes 0x00-0x24: game 1's docs/re/graphics.md; same engine here).

BT_UNITS     equ 0x80173278       ; [0x80196A20] 6 unit slots of 0x78 bytes: +0 hero id (slots 0-2), +0x16 > 0 = plate
BT_ETYPE     equ 0x8015D764       ; [0x80182B2C] u16 enemy type per enemy slot (slots 3-5)
BT_LOADIMAGE equ 0x800C61D8       ; [0x800EC6C0] LoadImage(RECT *, u32 *): queues the copy, keeps the pointer
BT_DRAWSYNC  equ 0x800C5F2C       ; [0x800EC414] DrawSync(0): wait for it before the buffer is reused
BT_DATA      equ 0x80115C64       ; [0x8013BFCC] old enemy name table, first 0x648 bytes (to 0x801162AC)
BT_NAMES     equ 0x80130008       ; [0x80153BE0] old descriptors of codes 0x25-0xBF, up to the code table 0x801310FC

.org 0x8001A680
btname_draw:
    addiu   sp, sp, -0x30
    sw      ra, 0x28(sp)
    sw      s0, 0x18(sp)           ; slot
    sw      s1, 0x1C(sp)           ; name pointer
    sw      s2, 0x20(sp)           ; pen x (pixels)
    sw      s3, 0x24(sp)           ; bt_font (data base)
    li      s3, bt_font
    move    s0, zero
@@slot:
    sll     t0, s0, 4
    subu    t0, t0, s0
    sll     t0, t0, 3              ; slot * 0x78
    li      t1, BT_UNITS
    addu    t0, t0, t1
    lh      t1, 0x16(t0)
    nop
    blez    t1, @@next
    sltiu   t2, s0, 3
    beqz    t2, @@enemy
    nop
    lh      t1, 0(t0)              ; hero id
    addiu   s1, s3, bt_hero - bt_font
    b       @@have
    sll     t1, t1, 4
@@enemy:
    sll     t2, s0, 1
    li      t3, BT_ETYPE - 6
    addu    t3, t3, t2
    lh      t1, 0(t3)
    li      s1, BT_NAMES
    sll     t1, t1, 4
@@have:
    addu    s1, s1, t1
    addiu   t0, s3, bt_buf - bt_font
    addiu   t1, t0, 256
@@clear:
    sw      zero, 0(t0)
    addiu   t0, t0, 4
    bne     t0, t1, @@clear
    nop
    move    s2, zero
@@char:
    lbu     t0, 0(s1)
    addiu   s1, s1, 1
    beqz    t0, @@load
    addiu   t0, t0, -0x20          ; glyph index
    addu    t2, s3, t0
    lbu     t3, 0(t2)              ; width
    sll     t4, t0, 3
    subu    t4, t4, t0
    addu    t4, t4, s3
    addiu   t4, t4, 96             ; 7 row bytes, bit 0 = leftmost pixel
    addiu   t5, s3, bt_buf - bt_font + 32  ; buffer row 1 (row 0 stays blank, as in the kana)
    li      t6, 7
@@row:
    lbu     t7, 0(t4)
    move    t8, s2
@@bit:
    beqz    t7, @@rowdone
    andi    t9, t7, 1
    beqz    t9, @@skip
    srl     t9, t8, 1
    addu    t9, t5, t9
    lbu     a0, 0(t9)
    andi    a1, t8, 1
    sll     a1, a1, 2
    li      a2, 1
    sllv    a2, a2, a1
    or      a0, a0, a2
    sb      a0, 0(t9)
@@skip:
    srl     t7, t7, 1
    b       @@bit
    addiu   t8, t8, 1
@@rowdone:
    addiu   t4, t4, 1
    addiu   t6, t6, -1
    bnez    t6, @@row
    addiu   t5, t5, 32
    addu    s2, s2, t3
    b       @@char
    addiu   s2, s2, 1
@@load:
    andi    t0, s0, 1
    sll     t0, t0, 4
    addiu   t0, t0, 0x1E0
    sh      t0, 0x10(sp)           ; RECT x (halfwords)
    srl     t0, s0, 1
    sll     t0, t0, 3
    addiu   t0, t0, 0x40
    sh      t0, 0x12(sp)           ; y
    li      t0, 0x80010
    sw      t0, 0x14(sp)           ; w 16 (64 px of 4bpp), h 8
    addiu   a0, sp, 0x10
    jal     BT_LOADIMAGE
    addiu   a1, s3, bt_buf - bt_font
    jal     BT_DRAWSYNC
    move    a0, zero
@@next:
    addiu   s0, s0, 1
    sltiu   t0, s0, 6
    bnez    t0, @@slot
    nop
    lw      ra, 0x28(sp)
    lw      s3, 0x24(sp)
    lw      s2, 0x20(sp)
    lw      s1, 0x1C(sp)
    lw      s0, 0x18(sp)
    jr      ra
    addiu   sp, sp, 0x30
btname_end:
.if btname_end > 0x8001A840
    .error "battle name routine is longer than the one it replaces"
.endif

.org BT_DATA
bt_font:
    .incbin BTFONT_BIN             ; 96 widths, then 96 x 7 rows (ASCII 0x20-0x7F)
bt_hero:
    .incbin BTHERO_BIN             ; 19 x 16 bytes, by hero id
.align 4
bt_buf:
    .fill 256                      ; 64 x 8 px, 4bpp
bt_data_end:
.if bt_data_end > 0x801162AC
    .error "battle name data overflows the old enemy name table"
.endif

.org BT_NAMES
    .incbin BTENEMY_BIN            ; 254 x 16 bytes, by enemy type (0-253)
bt_names_end:
.if bt_names_end > 0x801310FC
    .error "battle enemy names overflow into the font code table"
.endif

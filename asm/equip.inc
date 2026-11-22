; equip.inc: hero status screen, Equip box (Weapon/Armor/Other names) in the caps4x7 font. Game 1's
; (../favorite-dear-en/asm/equip.inc: its GitHub issue #2, its decision D21; here D-entry in docs/decisions.md),
; every address re-found by tools/codefind.py / tools/addrmap.py (game 1 in brackets). Assembled with btname.inc
; (asm/btname.asm, PSX.EXE only): it draws with that file's bt_font and bt_buf.
;
; 0x800E9C50 [0x80110CFC] (called from 0x800F5848 [0x8011CBFC] as the status screen opens) ClearImages a 256x200
; 4bpp sheet at VRAM (0x240 halfwords, 0) and, for the selected hero (s8 0x801942E9, 0-12), renders the name of
; each equipped item (u16 code at hero record 0x8018C680 [0x8001F6E4] + 0x6C * hero + 0x2A/0x2C/0x2E, 0xFFFF =
; none; string = *(0x80145CBC [0x80169778] + 4 * index), index from 0x80099208: code + 0x8C below 0xED, + 0x100
; below 0xF9, else + 0x144) with 0x800E9D90 [0x80110E58](str, x 0x240, y 0, 0) and the row offset 0x10/0x18/0x20
; at 0x10(sp). 0x800E9D90 copied one 8x8 cell of the small kana font per code (table 0x80193F30 [0x80026E18]),
; which has no Latin, so English names drew nothing. The screen then draws each row as a sprite (u 0, v
; 0x10/0x18/0x20, w 0x40, h 8) at x 0x50 (0x800E8594-0x800E8634 [0x8010F638-0x8010F6D8]).
;
; Now 0x800E9D90 is rewritten in place: it decodes the pair codes back to letters (low byte left, high byte right),
; upper-cases them and renders them in the battle name-plate font (bt_font: proportional, 7 rows, 1-px gaps, ink =
; colour 1 like the kana) into an 80x8 buffer (row 0 blank), then LoadImages it to the row. The three sprites are
; 80 px wide and start at x 77 (the labels moved to x 25, gfx/e014.tsv; "Weapon:" ends at 73): every equippable
; name fits before the box's inner edge at x 152 (tests/test_equip.py).

EQ_W      equ 80                  ; row width in pixels (sprite w, buffer width)
EQ_X      equ 77                  ; screen x of the names

.org 0x800E9D90
equip_draw:                        ; a0 = string, a1 = sheet x (halfwords), a2 = sheet y, a3 = 0, 0x10(sp) = row
    addiu   sp, sp, -0x30
    sw      ra, 0x28(sp)
    sw      s0, 0x18(sp)           ; string
    sw      s1, 0x1C(sp)           ; pen x (pixels)
    sw      s2, 0x20(sp)           ; halfword being drawn
    sw      s3, 0x24(sp)           ; bt_font (data base)
    lw      t0, 0x40(sp)           ; the caller's 0x10(sp): row offset
    move    s0, a0
    addu    a2, a2, t0
    sh      a1, 0x10(sp)           ; RECT x
    sh      a2, 0x12(sp)           ; RECT y
    li      t0, (8 << 16) | (EQ_W / 4)
    sw      t0, 0x14(sp)           ; w (halfwords), h 8
    li      s3, bt_font
    addiu   t0, s3, bt_buf - bt_font
    addiu   t1, t0, EQ_W / 2 * 8
@@clear:
    sw      zero, 0(t0)
    addiu   t0, t0, 4
    bne     t0, t1, @@clear
    nop
    move    s1, zero
@@half:
    lhu     s2, 0(s0)
    ori     t1, zero, 0xFEFE
    sltu    t1, t1, s2             ; {n} 0xFEFF or {end} 0xFFFF: done
    bnez    t1, @@load
    addiu   s0, s0, 2
@@byte:
    andi    t0, s2, 0xFF
    beqz    t0, @@half             ; both letters of this halfword drawn
    srl     s2, s2, 8
    addiu   t1, t0, -0x61
    sltiu   t1, t1, 26
    beqz    t1, @@upper
    nop
    addiu   t0, t0, -0x20          ; a-z -> A-Z
@@upper:
    addiu   t0, t0, -0x20          ; glyph index (ASCII 0x20-0x7F)
    sltiu   t1, t0, 96
    beqz    t1, @@byte             ; the en6x12 extras (0x80+) have no caps glyph
    addu    t2, s3, t0
    lbu     t3, 0(t2)              ; width
    sll     t4, t0, 3
    subu    t4, t4, t0
    addu    t4, t4, s3
    addiu   t4, t4, 96             ; 7 row bytes, bit 0 = leftmost pixel
    addiu   t5, s3, bt_buf - bt_font + EQ_W / 2   ; buffer row 1 (row 0 stays blank)
    li      t6, 7
@@row:
    lbu     t7, 0(t4)
    move    t8, s1
@@bit:
    beqz    t7, @@rowdone
    andi    t9, t7, 1
    beqz    t9, @@skip
    sltiu   a0, t8, EQ_W
    beqz    a0, @@skip             ; past the row: clip
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
    addiu   t5, t5, EQ_W / 2
    addu    s1, s1, t3
    b       @@byte
    addiu   s1, s1, 1
@@load:
    addiu   a0, sp, 0x10
    jal     BT_LOADIMAGE
    addiu   a1, s3, bt_buf - bt_font
    jal     BT_DRAWSYNC
    move    a0, zero
    lw      ra, 0x28(sp)
    lw      s3, 0x24(sp)
    lw      s2, 0x20(sp)
    lw      s1, 0x1C(sp)
    lw      s0, 0x18(sp)
    jr      ra
    addiu   sp, sp, 0x30
equip_end:
.if equip_end > 0x800E9EF4
    .error "equip.inc overflows the old small-font equipment renderer (0x800E9D90-0x800E9EF4)"
.endif

; The three row sprites (status screen draw, 0x800E8594-0x800E8634): w 0x40 -> EQ_W, x 0x50 -> EQ_X.
.org 0x800E8594
    addiu   a3, zero, EQ_W
.org 0x800E85A8
    addiu   a0, zero, EQ_X
.org 0x800E85E4
    addiu   a3, zero, EQ_W
.org 0x800E85F0
    addiu   a0, zero, EQ_X
.org 0x800E8628
    addiu   a3, zero, EQ_W
.org 0x800E8634
    addiu   a0, zero, EQ_X

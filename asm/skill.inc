; skill.inc: hero status screen, Special box (Skill 1-3) in the main font (docs/re/text.md §Hero skills).
;
; Game 1's (../favorite-dear-en/asm/skill.inc), every address re-found here (game 1 in brackets; disassembly and
; tools/codefind.py, 2026-11-22). 0x8009BD04 [0x800C337C] (called only from 0x800E869C/6D0/704 with a0 = skill
; string, a1 = x 0xE8, a2 = y 0xBC/0xC8/0xD4, a3 = colour 0x14) drew each code as an 8x8 cell of the small kana
; font, which has no Latin, so English names drew nothing. Now:
; - the status-text renderer 0x800E9EF4 [0x80110FBC] (it ClearImages a 256x256 VRAM sheet and renders the Name,
;   Birth and Sex strings into it with 0x800D67D0(str, x halfwords, y, 0)) also renders the three skills of the
;   hero (u16 table 0x8019AE84 + hero*6, 13 heroes; string = 0x801517C8 + 2*entry) at sheet rows 0x24, 0x30, 0x3C,
;   which the hero branch leaves empty (it uses rows 0, 0x0C, 0x18). The renderer differs from game 1's here
;   (heroes are chars 0-12 and 13-16 the first branch), so the hook is the hero branch's own exit 0x800EA1CC.
; - 0x8009BD04 is rewritten in place to draw that row as a sprite, the same way the Name is drawn at 0x800E87D0
;   (0x800F2114(object 0x46 = +0x118, u, v, w, h), then 0x800159D0), 12 px tall, at x = 0xE8 - 0x20 = 200
;   (the background labels are "1:" .. "3:", gfx/e014.tsv) so 16 letters (96 px) fit in the box.
; PSX.EXE only: OMK.EXE carries a copy of this screen (0x8009E834) that the Omake menu never opens.

SK_SHEET_Y0  equ 0x24             ; first sheet row used for skills
SK_SPRITE    equ 0x800F2114       ; [0x80119348] set object a0's texture rect (u, v, w, h = sp+0x10)
SK_DRAW      equ 0x800159D0       ; [0x8003D80C] draw it at (a0, a1)
SK_RENDER    equ 0x800D67D0       ; [0x800FD8C4] render string a0 into VRAM at (a1 halfwords, a2), a3 = 0
SK_STRLEN    equ 0x800D677C       ; [0x800FD870] glyph count of a string (codes <= 0xFEFF up to 0xFFFF)
SK_BASE      equ 0x80191C8C       ; [0x80024B74] sprite object base (+0x118 = status text sheet)
SK_HERO      equ 0x801942E9       ; [0x800271E9] s8 selected character
SK_TABLE     equ 0x8019AE84       ; [0x8002DBFC] u16 x 3 per hero: string offsets in halfwords from SK_STRINGS
SK_STRINGS   equ 0x801517C8       ; [0x80175C1C] = PSX.EXE file 0x141FC8 (script/exe.tsv PSX.141FC8..)
SK_CLUT      equ 0x80157F14       ; [0x8017C2E0] u16 passed by the Name draw as a2
SK_TPAGE     equ 0x80186C12       ; [0x80019C72] u16 passed by the Name draw at sp+0x14
SK_EXIT      equ 0x800EA2F8       ; [0x801113C4] the renderer's epilogue
SK_OLD_END   equ 0x8009BE4C       ; [0x800C34C4] end of the old drawer (jr ra + delay slot)

; --- end of the hero branch of the status-text renderer: was `j 0x800EA2F8 / nop` ---
.org 0x800EA1CC
    j       skill_render
    nop

.org 0x8009BD04
skill_draw:                        ; a0 = string, a1 = x, a2 = y, a3 = colour
    addiu   sp, sp, -0x30
    sw      ra, 0x2C(sp)
    sw      s0, 0x20(sp)
    sw      s1, 0x24(sp)
    sw      s2, 0x28(sp)
    move    s0, a1
    move    s1, a2
    jal     SK_STRLEN
    andi    s2, a3, 0xFFFF
    andi    v0, v0, 0xFFFF
    beqz    v0, @@out
    sll     a3, v0, 1
    addu    a3, a3, v0
    sll     a3, a3, 2              ; w = glyphs * 12
    li      t0, SK_BASE
    lw      a0, 0x118(t0)
    move    a1, zero
    addiu   a2, s1, SK_SHEET_Y0 - 0xBC   ; v: y 0xBC/0xC8/0xD4 -> rows 0x24/0x30/0x3C
    li      t1, 12
    jal     SK_SPRITE
    sw      t1, 0x10(sp)
    addiu   a0, s0, -0x20          ; x 0xE8 -> 200 (2 px after the "1:" label; 16 letters end at 296)
    addiu   a1, s1, -1             ; 12-px glyphs on the 12-px label rows (y 187/199/211)
    li      t0, SK_CLUT
    lhu     a2, 0(t0)
    li      a3, SK_BASE
    li      t1, 0x46               ; object 0x46 (+0x118), as the Name
    sw      t1, 0x10(sp)
    li      t0, SK_TPAGE
    lhu     t1, 0(t0)
    sw      s2, 0x18(sp)
    sw      t1, 0x14(sp)
    jal     SK_DRAW
    sw      zero, 0x1C(sp)
@@out:
    lw      ra, 0x2C(sp)
    lw      s2, 0x28(sp)
    lw      s1, 0x24(sp)
    lw      s0, 0x20(sp)
    jr      ra
    addiu   sp, sp, 0x30

skill_render:                      ; in 0x800E9EF4: s3 = sheet x (halfwords), s2 = sheet y; s0/s1 restored by its epilogue
    move    s0, zero
@@row:
    li      t0, SK_HERO
    lb      t1, 0(t0)
    nop
    sll     t2, t1, 1
    addu    t2, t2, t1
    sll     t2, t2, 1              ; hero * 6
    sll     t3, s0, 1
    addu    t2, t2, t3
    li      t0, SK_TABLE
    addu    t0, t0, t2
    lhu     t1, 0(t0)
    li      a0, SK_STRINGS
    sll     t1, t1, 1
    addu    a0, a0, t1
    sll     a1, s3, 16
    sra     a1, a1, 16
    sll     t1, s0, 1
    addu    t1, t1, s0
    sll     t1, t1, 2              ; row * 12
    addu    a2, s2, t1
    addiu   a2, a2, SK_SHEET_Y0
    sll     a2, a2, 16
    sra     a2, a2, 16
    jal     SK_RENDER
    move    a3, zero
    addiu   s0, s0, 1
    sltiu   t0, s0, 3
    bnez    t0, @@row
    nop
    j       SK_EXIT
    nop
skill_end:

.if skill_end > SK_OLD_END
    .error "skill.inc overflows the old small-font skill drawer (0x8009BD04-0x8009BE4C)"
.endif

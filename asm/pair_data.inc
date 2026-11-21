; pair_data.inc: the pair-glyph hook's data (asm/pair.inc): the 6x12 English font and the 12x24-byte scratch cell.
.align 4
pair_font:
    .incbin FONT_BIN
.align 4
pair_scratch:                      ; 12 rows x 24 bytes; only bytes 0-1 of each row are written
    .fill 12 * 24, 0

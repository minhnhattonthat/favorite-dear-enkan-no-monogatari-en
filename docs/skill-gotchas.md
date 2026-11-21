# Skill gotchas (one line each: the reference file it belongs in, then the fact)

- references/pipeline.md §Recon: on a re-release of an already-translated game, matching the old font's pixel rows found a false base (11 rows by chance); disassembling the old draw-glyph routine's twin (instruction match with immediates masked, `tools/codefind.py`) gave the real font pointer and showed the bit order had flipped (LSB-first -> MSB-first).
- references/pipeline.md §Recon: a sequel/re-release can change a directory's entry format (u32 sector + u32 bytes -> u16 sector + u16 count) while keeping entry indices; search for the old sector sequence at every width/stride, not just the old layout.

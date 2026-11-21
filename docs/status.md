# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build next (phase 4 extract done 2026-11-21, 4th worker).
- **Done:**
  - Step 0: template filled, `tools/skill.py`, PCSX-Redux in `tools/pcsx/` (fetch_emu), BIOS + mkpsxiso/armips/xdelta
    copied from game 1's repo, guard hook in `.claude/settings.json` (canary `sed -i` blocked), pre-commit hook
    (`core.hooksPath tools/hooks`, CHECK = `tools/check.py`; a failing test was rejected), `rom.sha1` +
    `tests/test_rom.py`, original disc smoke-boots to the title menu (`work/qa/smoke_orig`, scripted Start works).
    Not checked: keyboard input in the PCSX-Redux window (headless runs only).
  - Phase 1: **this game is an expanded re-release of game 1 (`../favorite-dear-en`)**. Same engine and layout,
    most data byte-identical, 56% of event characters are verbatim game-1 `jp` rows. Recorded in `docs/re/`:
    encoding (`tbl/jp.tbl`; font MSB-first at PSX.EXE 0xFA6C0; NCODES 0x6F0), GDATA/SDATA u16 directories, 568
    event scripts (game 1's grammar), EXE strings (952, also in OMK.EXE), credits in DATA/FIN.EXE, load buffer,
    graphics-text survey.
  - Phase 2: `tools/debug/` (warp.py/warp.lua/scenes.tsv, save.py, mcd.py, evnames.py), `docs/re/debug.md`,
    `tests/test_debug.py`, `tools/addrmap.py`. All 116 scenes reach their target from a cold boot on the original
    disc (`work/qa/warp/<scene>/arrived.png`, `results.tsv`): title/load/option menus, new game + name entry,
    week 1/2, world map, 30 game-1 events + 12 new ones (`--event eNNN`), hub + ability/map/system/save menus,
    7 battles + 12 T-battles, credits + full staff roll (FIN needs interpreter mode, automatic), epilog + endings
    1-26, ending movie, FD_BALL minigame, OMK Omake menu / Visual CG / Mini Event, edited save. Events are
    loaded by u16 name hash here (game 1: names); new events have no names, so GDATA entry eNNN is the handle.
    Game-written cards `work/saves/week1.mcd`, `week2.mcd` (gitignored; `save_write`/`save_write2` scenes
    regenerate them); save.py layout re-verified (second week copy at 0x2838), bad-sum save rejected.
  - Phase 3: `tools/build.py` (game 1's, adapted) -> `build/fd3_en_identity.bin/.cue` is byte-identical to the
    original (sha1 = `rom.sha1`, ~3 s, nothing to explain); `tests/test_build.py` (identity, one-byte edit changes
    one sector, unknown path refused; in the default check). The identity build smoke-boots
    (`work/qa/smoke_identity`) and `warp.py week1 --cue build/fd3_en_identity.cue --root work/qa/warp_identity`
    arrives (week-1 party screen). `build.py` without `--identity` exits until `tools/insert.py` exists (phase 7).
  - Phase 4: `tools/extract.py` (game 1's, adapted) -> `script/events/eNNN.tsv` (561 files, 12,617 rows, id
    `eNNN.<byte offset>`, NNN = GDATA entry; e902/e932 alias e520/e739), `script/exe.tsv` (885 rows: 2 regions,
    5 lui/addiu-addressed strings, 2 name-entry grids; OMK.EXE copies at fixed deltas, `extract.omk_delta`, same
    rows), `script/staff.tsv` (272 rows, FIN.EXE Shift-JIS lines), `script/sjis.tsv` (8 card titles).
    `tests/test_extract.py` (9 tests, in check): every row re-encodes to the original bytes (PSX and OMK), scripts
    tile end to end, EXE regions hold only rows/codes-only strings/3 pointer tables, staff roll rebuilds. Seeded
    from game 1's identical `jp` rows: 6,678 event + 852 EXE + 175 staff rows have game 1's `en` (`g1:<id>` in
    notes); 1,197 rows match game-1 glyph-soup rows game 1 never translated (notes say so). EXE text map and
    the sweep (`tools/strsweep.py`) in `docs/re/text.md`.
- **Next (phase 5, engine spike + marker build):** port game 1's English path: `en.py`/`font_en.py` (pair glyphs
  >= 0x2020, `EN_LO`), `insert.py` (events in place within the ~0x7000 load buffer, EXE strings in place or
  repointed via EXE_DATA tables; the 5 EXE_LOOSE strings need their lui/addiu patched if they grow; every EXE edit
  also into OMK.EXE), `wrap.py`, `fitcheck.py`, font MSB-first. Marker build `[id]` every row; tour with warp.py;
  measure each box variant (width gate, `docs/re/` window data); check the 1,197 glyph-soup rows (drawn or not)
  and the name-entry grids (game 1 D16: Latin page).
- **Known gaps (debug tool):** e964 (id 549) stalls in MYH16's context; how the title menu normally reaches
  OMK.EXE is untraced (the exec warp covers it); endings above 26 not tried; stress saves come in phase 8.
- **Open bugs:** none.
- **Waiting on the user:** nothing.

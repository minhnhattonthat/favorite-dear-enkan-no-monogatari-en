# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build in progress (pair glyphs boot in PSX/OMK/EPILOG; width gate for menus left; 5th worker).
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
  - Phase 5 so far: game 1's pair glyphs ported (`tools/en.py`, `tools/font_en.py` MSB-first, `fonts/en6x12.txt`,
    `asm/pair.inc`/`pair_data.inc`/`font.asm`/`epilog.asm`), `tools/insert.py` (modes en/marker/ruler/torture;
    events rebuilt + relocated to GDATA's end with all six u16 directories repointed; EXE strings in place in PSX
    and OMK; FIN staff roll markers in place), `build.py --mode`, `tests/test_insert.py` (6 tests, in check).
    Hook space: PSX 0x80192A6C / OMK 0x8019122C, proven unwritten by `tools/debug/freewatch.lua` (`space.md`).
    `build/fd3_en_marker.cue` smoke-boots (`work/qa/p5/smoke_marker`) and warps: ids render clean
    ("[e835.1F2A]The quick..."; title, week1, ev_kaiwa1). Ruler build: 14 scenes arrive (`work/qa/p5/ruler/`);
    measured dialogue 40, battle 40, endings 40 (EPILOG hook works) in `docs/windows.tsv`; credits show [Fn].
- **Next (phase 5, rest):** (1) measure the menu variants in `docs/windows.tsv` marked guess: add a
  single-string override (game 1 `--qa ID=text`-style, repointing the string through its EXE_DATA pointer) since
  the ruler build cuts EXE strings to their slot; hub help, location, ability list, week tags/action, save menu,
  confirm prompt/choice, angel name (`newgame_name10`), portrait vs no-portrait box. (2) torture build
  (`build.py --mode torture`, built, not booted): boot and check all 101 glyphs. (3) Glyph-soup rows: `warp.py
  --event e420` ends up in e453's dialogue (`work/qa/p5/soup`), so whether they draw is still open; try e573-e580
  and textcover. (4) Hero name ラビエル in the hub ability window stays Japanese: find its source (not in any TSV).
  (5) Watch EPILOG's blob address 0x80170000 in more endings (`freewatch.lua` with `--var FREE_RANGES=...`);
  re-run freewatch over minigame/omake/week2 for the PSX/OMK hook runs. (6) `wrap.py`/`fitcheck.py` from game 1.
- **Known gaps (debug tool):** e964 (id 549) stalls in MYH16's context; how the title menu normally reaches
  OMK.EXE is untraced (the exec warp covers it); endings above 26 not tried; stress saves come in phase 8.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
